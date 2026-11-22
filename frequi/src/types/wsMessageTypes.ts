export enum FtWsMessageTypes {
  exception = 'exception',

  whitelist = 'whitelist',
  entryFill = 'entry_fill',
  entryCancel = 'entry_cancel',

  exitFill = 'exit_fill',
  exitCancel = 'exit_cancel',
  newCandle = 'new_candle',
  /** Bot state changes (running / stopped / paused) and other status notes. */
  status = 'status',
}

export interface FtBaseWsMessage {
  type: FtWsMessageTypes;
}

export interface FtBaseEntryExitFillMessage extends FtBaseWsMessage {
  pair: string;
  open_rate: number;
  amount: number;
  direction: string;
  // ...
}

export interface FtWhitelistMessage extends FtBaseWsMessage {
  type: FtWsMessageTypes.whitelist;
  data: string[];
}

export interface FtEntryFillMessage extends FtBaseEntryExitFillMessage {
  type: FtWsMessageTypes.entryFill;
}

export interface FtExitFillMessage extends FtBaseEntryExitFillMessage {
  type: FtWsMessageTypes.exitFill;
}

export interface FTEntryCancelMessage extends FtBaseEntryExitFillMessage {
  type: FtWsMessageTypes.entryCancel;
  reason: string;
  // ...
}

export interface FTExitCancelMessage extends FtBaseEntryExitFillMessage {
  type: FtWsMessageTypes.exitCancel;
  reason: string;
  // ...
}

export interface FtNewCandleMessage extends FtBaseWsMessage {
  type: FtWsMessageTypes.newCandle;
  /** Pair, timeframe, candletype*/
  data: [string, string, string];
  // ...
}

export interface FtErrorMessage extends FtBaseWsMessage {
  type: FtWsMessageTypes.exception;
  data: string;
}

export interface FtStatusMessage extends FtBaseWsMessage {
  type: FtWsMessageTypes.status;
  status: string;
}

export type FTWsMessage =
  | FtErrorMessage
  | FtWhitelistMessage
  | FtEntryFillMessage
  | FTEntryCancelMessage
  | FtExitFillMessage
  | FTExitCancelMessage
  | FtNewCandleMessage
  | FtStatusMessage;
