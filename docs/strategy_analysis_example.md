# Strategy analysis example

Debugging a strategy can be time-consuming. Freqtrade offers helper functions to visualize raw data.
The following assumes you work with SampleStrategy, data for 5m timeframe from Binance and have downloaded them into the data directory in the default location.
Please follow the [documentation](https://www.freqtrade.io/en/stable/data-download/) for more details.

## Setup

### Change Working directory to repository root


```python
import os
from pathlib import Path


# Change directory
# Modify this cell to insure that the output shows the correct path.
# Define all paths relative to the project root shown in the cell output
project_root = "somedir/freqtrade"
i = 0
try:
    os.chdir(project_root)
    if not Path("LICENSE").is_file():
        i = 0
        while i < 4 and (not Path("LICENSE").is_file()):
            os.chdir(Path(Path.cwd(), "../"))
            i += 1
        project_root = Path.cwd()
except FileNotFoundError:
    print("Please define the project root relative to the current directory")
print(Path.cwd())
```

### Configure Freqtrade environment


```python
from freqtrade.configuration import Configuration


# Customize these according to your needs.

# Initialize empty configuration object
config = Configuration.from_files([])
# Optionally (recommended), use existing configuration file
# config = Configuration.from_files(["user_data/config.json"])

# Define some constants
config["timeframe"] = "5m"
# Name of the strategy class
config["strategy"] = "SampleStrategy"
# Location of the data
data_location = config["datadir"]
# Pair to analyze - Only use one pair here
pair = "BTC/USDT"
```


```python
# Load data using values set above
from freqtrade.data.history import load_pair_history
from freqtrade.enums import CandleType


candles = load_pair_history(
    datadir=data_location,
    timeframe=config["timeframe"],
    pair=pair,
    data_format="json",  # Make sure to update this to your data
    candle_type=CandleType.SPOT,
)

# Confirm success
print(f"Loaded {len(candles)} rows of data for {pair} from {data_location}")
candles.head()
```

## Load and run strategy
* Rerun each time the strategy file is changed


```python
# Load strategy using values set above
from freqtrade.data.dataprovider import DataProvider
from freqtrade.resolvers import StrategyResolver


strategy = StrategyResolver.load_strategy(config)
strategy.dp = DataProvider(config, None, None)
strategy.ft_bot_start()

# Generate buy/sell signals using strategy
df = strategy.analyze_ticker(candles, {"pair": pair})
df.tail()
```

### Display the trade details

* Note that using `data.head()` would also work, however most indicators have some "startup" data at the top of the dataframe.
* Some possible problems
    * Columns with NaN values at the end of the dataframe
    * Columns used in `crossed*()` functions with completely different units
* Comparison with full backtest
    * having 200 buy signals as output for one pair from `analyze_ticker()` does not necessarily mean that 200 trades will be made during backtesting.
    * Assuming you use only one condition such as, `df['rsi'] < 30` as buy condition, this will generate multiple "buy" signals for each pair in sequence (until rsi returns > 29). The bot will only buy on the first of these signals (and also only if a trade-slot ("max_open_trades") is still available), or on one of the middle signals, as soon as a "slot" becomes available.  



```python
# Report results
print(f"Generated {df['enter_long'].sum()} entry signals")
data = df.set_index("date", drop=False)
data.tail()
```

## Load existing objects into a Jupyter notebook

The following cells assume that you have already generated data using the cli.  
They will allow you to drill deeper into your results, and perform analysis which otherwise would make the output very difficult to digest due to information overload.

### Load backtest results to pandas dataframe

Analyze a trades dataframe


```python
from freqtrade.data.btanalysis import load_backtest_data, load_backtest_stats


# if backtest_dir points to a directory, it'll automatically load the last backtest file.
backtest_dir = config["user_data_dir"] / "backtest_results"
# backtest_dir can also point to a specific file
# backtest_dir = (
#   config["user_data_dir"] / "backtest_results/backtest-result-2020-07-01_20-04-22.json"
# )
```


```python
# You can get the full backtest statistics by using the following command.
# This contains all information used to generate the backtest result.
stats = load_backtest_stats(backtest_dir)

strategy = "SampleStrategy"
# All statistics are available per strategy, so if `--strategy-list` was used during backtest,
# this will be reflected here as well.
# Example usages:
print(stats["strategy"][strategy]["results_per_pair"])
# Get pairlist used for this backtest
print(stats["strategy"][strategy]["pairlist"])
# Get market change (average change of all pairs from start to end of the backtest period)
print(stats["strategy"][strategy]["market_change"])
# Maximum drawdown ()
print(stats["strategy"][strategy]["max_drawdown_abs"])
# Maximum drawdown start and end
print(stats["strategy"][strategy]["drawdown_start"])
print(stats["strategy"][strategy]["drawdown_end"])


# Get strategy comparison (only relevant if multiple strategies were compared)
print(stats["strategy_comparison"])
```


```python
# Load backtested trades as dataframe
trades = load_backtest_data(backtest_dir)

# Show value-counts per pair
trades.groupby("pair")["exit_reason"].value_counts()
```

### Load live trading results into a pandas dataframe

In case you did already some trading and want to analyze your performance


```python
from freqtrade.data.btanalysis import load_trades_from_db


# Fetch trades from database
trades = load_trades_from_db("sqlite:///tradesv3.sqlite")

# Display results
trades.groupby("pair")["exit_reason"].value_counts()
```

## Analyze the loaded trades for trade parallelism
This can be useful to find the best `max_open_trades` parameter, when used with backtesting in conjunction with a very high `max_open_trades` setting.

`analyze_trade_parallelism()` returns a timeseries dataframe with an "open_trades" column, specifying the number of open trades for each candle.


```python
from freqtrade.data.btanalysis import analyze_trade_parallelism


# Analyze the above
parallel_trades = analyze_trade_parallelism(trades, "5m")

parallel_trades.plot()
```

Feel free to submit an issue or Pull Request enhancing this document if you would like to share ideas on how to best analyze the data.
