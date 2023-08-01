# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib


class JumschBBpBAO(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '1h'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.1,
        "30": 0.2,
        "0": 0.4
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 20

    # Strategy parameters
    # buy_rsi = IntParameter(10, 40, default=30, space="buy")
    # sell_rsi = IntParameter(60, 90, default=70, space="sell")


    # aroon_osc_high = IntParameter(0,100,default=80,space="sell")
    # aroon_osc_low = IntParameter(-100,0,default=-80,space="buy")


    # buy_BBpB_high = IntParameter(50,150,default=100,space="buy")
    # sell_BBpB_low = IntParameter(-50,50,default=0,space="sell")

    buy_BBpB_low = IntParameter(-150,50,default=0,space="buy")
    # sell_BBpB_high = IntParameter(50,150,default=100,space="sell")
    sell_BBpB_high = IntParameter(99,101,default=103,space="sell")

    # buy_AO_low = IntParameter(-200,0,default=-100,space="buy")
    sell_AO_high = IntParameter(-10,10,default=0,space="sell")


    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    @property
    def plot_config(self):
        return {
            # Main plot indicators (Moving averages, ...)
            'main_plot': {
                'tema': {'color':'orange'},
                'sar': {'color': 'white'},
                'sma200':{'color':'black'}
            },
            'subplots': {
                # Subplots - each dict defines one additional plot
                "AROONOSC": {
                    'aroonosc': {'color': 'blue'},
                },
                "BBpB": {
                    'bb_percent': {'color': 'green'},
                }
            }
        }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Momentum Indicators
        # ------------------------------------
        # Awesome Oscillator
        dataframe['ao'] = qtpylib.awesome_oscillator(dataframe)
        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        # Aroon, Aroon Oscillator
        aroon = ta.AROON(dataframe)
        dataframe['aroonup'] = aroon['aroonup']
        dataframe['aroondown'] = aroon['aroondown']
        dataframe['aroonosc'] = ta.AROONOSC(dataframe)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Stochastic Fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']


        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # MFI
        dataframe['mfi'] = ta.MFI(dataframe)


                # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe["bb_percent"] = (
            (dataframe["close"] - dataframe["bb_lowerband"]) /
            (dataframe["bb_upperband"] - dataframe["bb_lowerband"])
        )
        dataframe["bb_width"] = (
            (dataframe["bb_upperband"] - dataframe["bb_lowerband"]) / dataframe["bb_middleband"]
        )

        # Bollinger Bands - Weighted (EMA based instead of SMA)
        # weighted_bollinger = qtpylib.weighted_bollinger_bands(
        #     qtpylib.typical_price(dataframe), window=20, stds=2
        # )
        # dataframe["wbb_upperband"] = weighted_bollinger["upper"]
        # dataframe["wbb_lowerband"] = weighted_bollinger["lower"]
        # dataframe["wbb_middleband"] = weighted_bollinger["mid"]
        # dataframe["wbb_percent"] = (
        #     (dataframe["close"] - dataframe["wbb_lowerband"]) /
        #     (dataframe["wbb_upperband"] - dataframe["wbb_lowerband"])
        # )
        # dataframe["wbb_width"] = (
        #     (dataframe["wbb_upperband"] - dataframe["wbb_lowerband"]) / dataframe["wbb_middleband"]
        # )


        # # EMA - Exponential Moving Average
        # dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        # dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        # dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)
        # dataframe['ema21'] = ta.EMA(dataframe, timeperiod=21)
        # dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        # dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        # # SMA - Simple Moving Average
        # dataframe['sma3'] = ta.SMA(dataframe, timeperiod=3)
        # dataframe['sma5'] = ta.SMA(dataframe, timeperiod=5)
        # dataframe['sma10'] = ta.SMA(dataframe, timeperiod=10)
        # dataframe['sma21'] = ta.SMA(dataframe, timeperiod=21)
        # dataframe['sma50'] = ta.SMA(dataframe, timeperiod=50)
        dataframe['sma200'] = ta.SMA(dataframe, timeperiod=200)

        # Parabolic SAR
        dataframe['sar'] = ta.SAR(dataframe)

        # TEMA - Triple Exponential Moving Average
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=9)

        # Cycle Indicator
        # ------------------------------------
        # Hilbert Transform Indicator - SineWave
        hilbert = ta.HT_SINE(dataframe)
        dataframe['htsine'] = hilbert['sine']
        dataframe['htleadsine'] = hilbert['leadsine']



        # custom indicator
        dataframe['ao_sma10'] = ta.SMA(dataframe['ao'], timeperiod=10)
        dataframe['ao_sma50'] = ta.SMA(dataframe['ao'], timeperiod=50)
        dataframe['ao_sma100'] = ta.SMA(dataframe['ao'], timeperiod=100)
        dataframe['ao_sma200'] = ta.SMA(dataframe['ao'], timeperiod=200)
        dataframe['ao_sma300'] = ta.SMA(dataframe['ao'], timeperiod=300)
        dataframe['ao_sma500'] = ta.SMA(dataframe['ao'], timeperiod=500)


        dataframe['ao_ema10'] = ta.EMA(dataframe['ao'], timeperiod=10)
        dataframe['ao_ema50'] = ta.EMA(dataframe['ao'], timeperiod=50)
        dataframe['ao_ema100'] = ta.EMA(dataframe['ao'], timeperiod=100)
        dataframe['ao_ema200'] = ta.EMA(dataframe['ao'], timeperiod=200)
        dataframe['ao_ema300'] = ta.EMA(dataframe['ao'], timeperiod=300)
        dataframe['ao_ema500'] = ta.EMA(dataframe['ao'], timeperiod=500)

        dataframe['ao_ema10_adj'] = -dataframe['ao_ema10']+(abs(dataframe['ao_ema10'])*self.sell_AO_high.value)
        dataframe['ao_ema10_ema10_adj'] = -dataframe['ao_ema10'].mul(dataframe['ao_ema10'])+(abs(dataframe['ao_ema10'])*self.sell_AO_high.value)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_above(dataframe['bb_percent'], float(self.buy_BBpB_low.value)/100)) &
                (dataframe['ao']<dataframe['ao_ema10_adj'])&
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'enter_long'] = 1
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)

        # dataframe.loc[
        #     (
        #         (qtpylib.crossed_below(dataframe['aroonosc'], self.aroon_osc_high.value)) &  # Signal: RSI crosses above buy_rsi
        #         (dataframe['volume'] > 0)  # Make sure Volume is not 0
        #     ),
        #     'enter_short'] = 1


        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (qtpylib.crossed_below(dataframe['bb_percent'], float(self.sell_BBpB_high.value)/100)) &
                (dataframe['ao']>(dataframe['ao_ema10_adj']))&
                (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'exit_long'] = 1
        # Uncomment to use shorts (Only used in futures/margin mode. Check the documentation for more info)

        # dataframe.loc[
        #     (
        #         (qtpylib.crossed_above(dataframe['aroonosc'], self.aroon_osc_low.value)) &  # Signal: RSI crosses above buy_rsi
        #         (dataframe['volume'] > 0)  # Make sure Volume is not 0
        #     ),
        #     'exit_short'] = 1

        return dataframe

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        """
        Called at the start of the bot iteration (one loop).
        Might be used to perform pair-independent tasks
        (e.g. gather some remote ressource for comparison)

        For full documentation please go to https://www.freqtrade.io/en/latest/strategy-advanced/

        When not implemented by a strategy, this simply does nothing.
        :param current_time: datetime object, containing the current datetime
        :param **kwargs: Ensure to keep this here so updates to this won't break your strategy.
        """
        pass