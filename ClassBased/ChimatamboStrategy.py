import numpy
from Trade import Trade
import logging, json, sys, time, configparser
from talib.abstract import *
import pandas 
import multiprocessing

class ChimatamboStrategy(Trade):

    def __init__(self, risk_management, stake, expiration, account_type) -> None:
        super().__init__(risk_management, stake, expiration, account_type)
    
    def start(self,symbol,timeframe,option):
        crossover_up = False
        crossover_down = False
        upper_bb_touch = False
        lower_bb_touch = False
        self.API.start_candles_stream(symbol,int(timeframe),280)
        while True:
            try:
                close_price = self.getClosePrices(symbol,timeframe)
                ma8 = WMA(close_price, timeperiod=8)[-1]
                ma14 = WMA(close_price, timeperiod=14)[-1]
                upperband, middleband, lowerband = BBANDS(close_price, timeperiod=14, nbdevup=2.0, nbdevdn=2.0, matype=0)
            except KeyError:
                pass
            else:                
                remaining_time=self.API.get_remaning(self.expiration)
                print(f"{symbol} , CROSS UP:{crossover_up} CROSS DOWN: {crossover_down}=> BB UPPER = {upperband[-1]} | BB LOWER =  {lowerband[-1]} | PRICE = {close_price[-1]}")
                close = close_price
                # print(close_price)
                if ma8 > ma14:
                    crossover_up = True
                    crossover_down = False
                    print (f"{symbol} Cross Up : True")
                    
                elif ma8 < ma14:
                    crossover_down = True
                    crossover_up = False
                    print (f"{symbol} Cross Down : True")
                
                if close[-1] >= upperband[-1]:
                    upper_bb_touch = True
                    lower_bb_touch = False
                    print (f"{symbol} UP BB Touch : True")

                elif close[-1] <= lowerband[-1]:
                    upper_bb_touch = False
                    lower_bb_touch = True
                    print (f"{symbol} DOWN BB Touch : True")
                
                if close[-1] <= ma8 and crossover_up == True and upper_bb_touch == True and remaining_time == 60:
                    print (f"{symbol} Signal Call")
                    self.trade(symbol,"call",option)
                    crossover_up = False
                    upper_bb_touch = False

                elif close[-1] >= ma8 and crossover_down == True and lower_bb_touch == True and remaining_time == 60:
                    print (f"{symbol} Signal Put")
                    self.trade(symbol,"put",option) 
                    crossover_down = False
                    lower_bb_touch = False






"""YOU CAN ONLY EDIT VALUES OF THE VARIABLE BELOW"""

risk_management = {
    "maximum_risk_target":float(100000), #Balance you want to reach due to profit
    "maximum_risk_":float(0), # Balance you want to reach due to loss
    "stake_percentage" : float(10),
    "risk_type" : str("balance_percentage") # flat #martingale #compound_all #compund_profit_only #balance_percentage 
} 
account_type    = "PRACTICE" # / REAL / PRACTICE /TOURNAMENT /TOURNAMENT APRIL TOURNAMENT/ IQ LAUNCH /RAMADAN
stake           = float(1)
expiration      = int(1)
timeframe       = int(60)
period          = int(14) # BB Period
std             = float(2) #Standard deviation
option          = "digital" 

trade = ChimatamboStrategy(risk_management, stake, expiration,account_type)

symbols = ["EURUSD-OTC","EURJPY-OTC","EURGBP-OTC","GBPUSD-OTC","GBPJPY-OTC","USDJPY-OTC","USDCHF-OTC","USDZAR-OTC","NZDUSD-OTC","USDXOF-OTC","USDSGD-OTC"]

for symbol in symbols:
    multiprocessing.Process(target=trade.start, args = (symbol,timeframe,option)).start()

#start time: 03:38