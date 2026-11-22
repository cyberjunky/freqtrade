"""
Main Freqtrade worker class.
"""

import logging
import time
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from os import getpid
from typing import Any

import sdnotify
from sqlalchemy.exc import SQLAlchemyError

from freqtrade import __version__
from freqtrade.configuration import Configuration
from freqtrade.constants import PROCESS_THROTTLE_SECS, RETRY_TIMEOUT, Config
from freqtrade.enums import RPCMessageType, State
from freqtrade.exceptions import OperationalException, TemporaryError
from freqtrade.exchange import timeframe_to_next_date
from freqtrade.freqtradebot import FreqtradeBot
from freqtrade.persistence import KeyValueStore, Trade
from freqtrade.persistence.storage_health import (
    format_bytes,
    lowest_free_space,
    storage_error_reason,
    storage_paths,
)


logger = logging.getLogger(__name__)

# Number of consecutive unexpected bot-loop failures after which trading is stopped.
MAX_CONSECUTIVE_LOOP_ERRORS = 5
# Free disk space below which a warning is sent, how often it is checked, and how often the
# warning may repeat.
LOW_DISK_WARNING_BYTES = 1024**3
DISK_CHECK_INTERVAL_SECS = 600
LOW_DISK_REPEAT_SECS = 6 * 3600


class Worker:
    """
    Freqtradebot worker class
    """

    def __init__(self, args: dict[str, Any], config: Config | None = None) -> None:
        """
        Init all variables and objects the bot needs to work
        """
        logger.info(f"Starting worker {__version__}")

        self._args = args
        self._config = config
        self._init(False)

        self._heartbeat_msg: float = 0
        self._consecutive_errors = 0
        # Set while the database cannot be written (disk full, read-only, ...): trading pauses.
        self._storage_down_since: float | None = None
        self._storage_reason = ""
        self._last_disk_check: float = 0
        self._low_disk_warned: float = 0

        # Tell systemd that we completed initialization phase
        self._notify("READY=1")

    def _init(self, reconfig: bool) -> None:
        """
        Also called from the _reconfigure() method (with reconfig=True).
        """
        if reconfig or self._config is None:
            # Load configuration
            self._config = Configuration(self._args, None).get_config()

        # Init the instance of the bot
        self.freqtrade = FreqtradeBot(self._config)

        internals_config = self._config.get("internals", {})
        self._throttle_secs = internals_config.get("process_throttle_secs", PROCESS_THROTTLE_SECS)
        self._heartbeat_interval = internals_config.get("heartbeat_interval", 60)

        self._sd_notify = (
            sdnotify.SystemdNotifier()
            if self._config.get("internals", {}).get("sd_notify", False)
            else None
        )

    def _notify(self, message: str) -> None:
        """
        Removes the need to verify in all occurrences if sd_notify is enabled
        :param message: Message to send to systemd if it's enabled.
        """
        if self._sd_notify:
            logger.debug(f"sd_notify: {message}")
            self._sd_notify.notify(message)

    def run(self) -> None:
        state = None
        while True:
            state = self._worker(old_state=state)
            if state == State.RELOAD_CONFIG:
                self._reconfigure()

    def _worker(self, old_state: State | None) -> State:
        """
        The main routine that runs each throttling iteration and handles the states.
        :param old_state: the previous service state from the previous call
        :return: current service state
        """
        state = self.freqtrade.state

        # Log state transition
        if state != old_state:
            if old_state != State.RELOAD_CONFIG:
                self.freqtrade.notify_status(f"{state.name.lower()}")

            logger.info(
                f"Changing state{f' from {old_state.name}' if old_state else ''} to: {state.name}"
            )
            if state in (State.RUNNING, State.PAUSED) and old_state not in (
                State.RUNNING,
                State.PAUSED,
            ):
                self.freqtrade.startup()

            if state == State.STOPPED:
                self.freqtrade.check_for_open_trades()

            # Reset heartbeat timestamp to log the heartbeat message at
            # first throttling iteration when the state changes
            self._heartbeat_msg = 0

        if state == State.STOPPED:
            # Ping systemd watchdog before sleeping in the stopped state
            self._notify("WATCHDOG=1\nSTATUS=State: STOPPED.")

            self._throttle(func=self._process_stopped, throttle_secs=self._throttle_secs)

        elif state in (State.RUNNING, State.PAUSED):
            state_str = "RUNNING" if state == State.RUNNING else "PAUSED"
            # Ping systemd watchdog before throttling
            self._notify(f"WATCHDOG=1\nSTATUS=State: {state_str}.")

            # Use an offset of 1s to ensure a new candle has been issued
            self._throttle(
                func=self._process_running,
                throttle_secs=self._throttle_secs,
                timeframe=self._config["timeframe"] if self._config else None,
                timeframe_offset=1,
            )

        if self._heartbeat_interval:
            now = time.time()
            if (now - self._heartbeat_msg) > self._heartbeat_interval:
                version = __version__
                strategy_version = self.freqtrade.strategy.version()
                if strategy_version is not None:
                    version += ", strategy_version: " + strategy_version
                logger.info(
                    f"Bot heartbeat. PID={getpid()}, version='{version}', state='{state.name}'"
                )
                self._heartbeat_msg = now

        return state

    def _throttle(
        self,
        func: Callable[..., Any],
        throttle_secs: float,
        timeframe: str | None = None,
        timeframe_offset: float = 1.0,
        *args,
        **kwargs,
    ) -> Any:
        """
        Throttles the given callable that it
        takes at least `min_secs` to finish execution.
        :param func: Any callable
        :param throttle_secs: throttling iteration execution time limit in seconds
        :param timeframe: ensure iteration is executed at the beginning of the next candle.
        :param timeframe_offset: offset in seconds to apply to the next candle time.
        :return: Any (result of execution of func)
        """
        last_throttle_start_time = time.time()
        logger.debug("========================================")
        result = func(*args, **kwargs)
        time_passed = time.time() - last_throttle_start_time
        sleep_duration = throttle_secs - time_passed
        if timeframe:
            next_tf = timeframe_to_next_date(timeframe)
            # Maximum throttling should be until new candle arrives
            # Offset is added to ensure a new candle has been issued.
            next_tft = next_tf.timestamp() - time.time()
            next_tf_with_offset = next_tft + timeframe_offset
            if next_tft < sleep_duration < next_tf_with_offset:
                # Avoid hitting a new loop between the new candle and the candle with offset
                sleep_duration = next_tf_with_offset
            sleep_duration = min(sleep_duration, next_tf_with_offset)
        sleep_duration = max(sleep_duration, 0.0)
        # next_iter = datetime.now(timezone.utc) + timedelta(seconds=sleep_duration)

        logger.debug(
            f"Throttling with '{func.__name__}()': sleep for {sleep_duration:.2f} s, "
            f"last iteration took {time_passed:.2f} s."
            #  f"next: {next_iter}"
        )
        self._sleep(sleep_duration)
        return result

    @staticmethod
    def _sleep(sleep_duration: float) -> None:
        """Local sleep method - to improve testability"""
        time.sleep(sleep_duration)

    def _process_stopped(self) -> None:
        self.freqtrade.process_stopped()

    def _process_running(self) -> None:
        if self._storage_down_since is not None and not self._storage_recovered():
            time.sleep(RETRY_TIMEOUT)
            return
        self._check_free_disk()
        try:
            self.freqtrade.process()
            self._consecutive_errors = 0
        except TemporaryError as error:
            logger.warning(f"Error: {error}, retrying in {RETRY_TIMEOUT} seconds...")
            time.sleep(RETRY_TIMEOUT)
        except OperationalException:
            tb = traceback.format_exc()
            hint = "Issue `/start` if you think it is safe to restart."

            self.freqtrade.notify_status(
                f"*OperationalException:*\n```\n{tb}```\n {hint}", msg_type=RPCMessageType.EXCEPTION
            )

            logger.exception("OperationalException. Stopping trader ...")
            self.freqtrade.state = State.STOPPED
        except Exception as error:
            if reason := storage_error_reason(error):
                self._rollback_session()
                self._storage_failed(reason, error)
                time.sleep(RETRY_TIMEOUT)
                return
            # Any other failure (e.g. a PricingError while replacing an order) used to end the
            # process, leaving open positions unmanaged. Keep managing them instead, but stop
            # trading if the error keeps repeating.
            self._consecutive_errors += 1
            if isinstance(error, SQLAlchemyError):
                # A failed flush leaves the session unusable until rolled back. Other errors
                # deliberately keep pending changes: they may record an order that already
                # exists on the exchange.
                self._rollback_session()
            logger.exception(
                f"Unexpected error in bot loop ({self._consecutive_errors}/"
                f"{MAX_CONSECUTIVE_LOOP_ERRORS}): {error!r}"
            )
            if self._consecutive_errors >= MAX_CONSECUTIVE_LOOP_ERRORS:
                tb = traceback.format_exc()
                hint = "Issue `/start` if you think it is safe to restart."
                self.freqtrade.notify_status(
                    f"*Repeated unexpected error:*\n```\n{tb}```\n {hint}",
                    msg_type=RPCMessageType.EXCEPTION,
                )
                logger.error("Too many consecutive errors. Stopping trader ...")
                self._consecutive_errors = 0
                self.freqtrade.state = State.STOPPED
            else:
                time.sleep(RETRY_TIMEOUT)

    def _free_space_text(self) -> str:
        lowest = lowest_free_space(storage_paths(self._config or {}))
        if lowest is None:
            return "free space unknown"
        return f"{format_bytes(lowest[1])} free on {lowest[0]}"

    def _storage_failed(self, reason: str, error: Exception) -> None:
        """
        The database cannot be written. Placing orders now could leave orders on the exchange
        that the bot does not know about (and would place again), so pause all trading until a
        test write succeeds - no manual restart needed.
        """
        if self._storage_down_since is not None:
            return
        self._storage_down_since = time.time()
        self._storage_reason = reason
        self._consecutive_errors = 0
        logger.error(
            f"Database cannot be written ({reason}): {error!r}. "
            f"Trading paused until it can be written again."
        )
        self.freqtrade.notify_status(
            f"*Database cannot be written:* {reason} ({self._free_space_text()}).\n"
            f"Trading is paused: no orders are placed and open trades are not managed until "
            f"the database can be saved again. Checked every {RETRY_TIMEOUT} s; the bot resumes "
            f"by itself (no /start needed). Free disk space or fix the database to recover.",
            msg_type=RPCMessageType.EXCEPTION,
        )

    def _storage_recovered(self) -> bool:
        """Test write to the database; on success resume trading."""
        try:
            KeyValueStore.store_value("db_write_check", datetime.now(UTC))
        except Exception as error:
            self._rollback_session()
            logger.warning(
                f"Database still cannot be written ({storage_error_reason(error) or error!r}), "
                f"trading stays paused."
            )
            return False
        minutes = (time.time() - (self._storage_down_since or time.time())) / 60
        self._storage_down_since = None
        logger.info(f"Database can be written again after {minutes:.0f} min, trading resumes.")
        self.freqtrade.notify_status(
            f"Database can be written again after {minutes:.0f} min "
            f"(was: {self._storage_reason}, now {self._free_space_text()}). Trading resumes."
        )
        return True

    def _check_free_disk(self) -> None:
        """Warn before the disk is full, while there is still time to act."""
        now = time.time()
        if now - self._last_disk_check < DISK_CHECK_INTERVAL_SECS:
            return
        self._last_disk_check = now
        lowest = lowest_free_space(storage_paths(self._config or {}))
        if lowest is None or lowest[1] >= LOW_DISK_WARNING_BYTES:
            return
        if now - self._low_disk_warned < LOW_DISK_REPEAT_SECS:
            return
        self._low_disk_warned = now
        msg = (
            f"Low disk space: {format_bytes(lowest[1])} free on {lowest[0]}. When it runs out "
            f"the database cannot be saved and trading pauses."
        )
        logger.warning(msg)
        self.freqtrade.notify_status(msg, msg_type=RPCMessageType.WARNING)

    @staticmethod
    def _rollback_session() -> None:
        """Reset the database session after a database error."""
        try:
            Trade.rollback()
        except Exception:
            logger.exception("Could not roll back the database session.")

    def _reconfigure(self) -> None:
        """
        Cleans up current freqtradebot instance, reloads the configuration and
        replaces it with the new instance
        """
        # Tell systemd that we initiated reconfiguration
        self._notify("RELOADING=1")

        # Clean up current freqtrade modules
        self.freqtrade.cleanup()

        # Load and validate config and create new instance of the bot
        self._init(True)

        self.freqtrade.notify_status(f"{State(self.freqtrade.state)} after config reloaded")

        # Tell systemd that we completed reconfiguration
        self._notify("READY=1")

    def exit(self) -> None:
        # Tell systemd that we are exiting now
        self._notify("STOPPING=1")

        if self.freqtrade:
            self.freqtrade.notify_status("process died")
            self.freqtrade.cleanup()
