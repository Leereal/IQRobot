from datetime import datetime, timedelta

import numpy
from Trade import Trade
import logging, json, sys, time, configparser
from talib.abstract import *
import pandas 

class BBStrategy(Trade):
    """Bollinger Band Strategy - BB 14, 2"""
    def __init__(self, risk_management, stake, expiration, account_type) -> None:
        super().__init__(risk_management, stake, expiration, account_type)
    
    def bollinger_bands(self,s, n=14, k=2):
        """get_bollinger_bands DataFrame
        s is series of values
        k is multiple of standard deviations
        n is rolling window
        """

        b = pandas.concat([s, s.rolling(n).agg([numpy.mean, numpy.std])], axis=1)
        b['upper'] = b['mean'] + b['std'] * k
        b['lower'] = b['mean'] - b['std'] * k

        return b.drop('std', axis=1)
      
    
    def start(self,symbol,option,bb_period,timeframe,std):
        """Place a trade based on BB Rules rules"""
     
        maxdict = 280

        call_wait = True
        put_wait = True

        print(f"|+|====================Bollinger Band Strategy started on {symbol}==================|+|")

        self.API.start_candles_stream(symbol,int(timeframe),maxdict)     
        while True:            
            try: 
                # close = self.getClosePrices(symbol,timeframe)        
                # upperband, middleband, lowerband = BBANDS(close, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0) 
                candles = self.API.get_realtime_candles(symbol, timeframe)	
                df_time = pandas.DataFrame([(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), candles[ts]["close"], candles[ts]["max"], candles[ts]["min"]) for ts in sorted(candles.keys(), reverse=True)], columns=['from', 'close', 'max', 'min']).set_index('from')
                df_time = df_time.sort_index(ascending=False)
                
                df_time_close = df_time['close']
             
                bbands = self.bollinger_bands(df_time_close.iloc[0:14], bb_period, std) 

                bb_hi = round(bbands.iloc[-1]['upper'], 6) #bollinger band 
                bb_lw = round(bbands.iloc[-1]['lower'], 6)
                curr_price = df_time_close.iloc[0]

            except KeyError:
                pass

            else:
                print(f"{symbol} , PUT:{put_wait} CALL: {call_wait}=> BB UPPER = {bb_hi} | BB LOWER =  {bb_lw} | PRICE = {curr_price}")
                remaining_time=self.API.get_remaning(self.expiration)

                if curr_price < bb_lw  and  remaining_time == 61 and call_wait == True :                    
                    self.trade(symbol,"call",option)
                    print("BUY SIGNAL")
                    time.sleep(10)
                    call_wait = False
                    put_wait = True

                #Condition for a put
                elif curr_price > bb_hi and  remaining_time == 61 and put_wait ==  True :
                    self.trade(symbol,"put",option)
                    print("SELL SIGNAL")
                    time.sleep(10)
                    call_wait = True
                    put_wait = False







"""YOU CAN ONLY EDIT VALUES OF THE VARIABLE BELOW"""

risk_management = {
    "maximum_risk_target":float(100000), #Balance you want to reach due to profit
    "maximum_risk_":float(25), # Balance you want to reach due to loss
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

trade = BBStrategy(risk_management, stake, expiration,account_type)
# trade.start("EURUSD","call",period,timeframe,std)   
# trade.start("EURJPY",option,period,timeframe,std) 
# trade.start("EURGBP",option,period,timeframe,std) 
trade.start("GBPUSD",option,period,timeframe,std) 
# trade.start("GBPJPY",option,period,timeframe,std) 
# trade.start("AUDUSD",option,period,timeframe,std) 
# trade.start("USDCAD",option,period,timeframe,std) 
# trade.start("USDJPY",option,period,timeframe,std) 

    


