from Trade import Trade
import logging, json, sys, time, configparser
from talib.abstract import *
import multiprocessing

class RsiStrategy(Trade):

    def __init__(self,risk_management, stake, expiration, account_type) -> None:
        super().__init__(risk_management, stake, expiration, account_type)   
           
    
    def start(self,symbol,option,overbought,oversold,timeframe):
        """Place a trade based on RSI rules"""      
        maxdict = 280

        print(f"|+|====================RSI Strategy started on {symbol}==================|+|")

        self.API.start_candles_stream(symbol,int(timeframe),maxdict)
        
        while True:

            try:            
                rsi_value = RSI(self.getClosePrices(symbol,timeframe), timeperiod=14)[-1] #Get the last RSI value

            except KeyError:
                pass

            else:
                print(f"SYMBOL : {symbol} | RSI :  {round(rsi_value, 2)}") 

                #RSI Check               
                if rsi_value >= overbought :
                    self.trade(symbol,"put",option)

                elif rsi_value <= oversold : 
                    self.trade(symbol,"call",option)
            
            



"""YOU CAN ONLY EDIT VALUES OF THE VARIABLE BELOW"""

risk_management = {
    "maximum_risk_target":float(100), #Balance you want to reach due to profit
    "maximum_risk_":float(0), # Balance you want to reach due to loss
    "stake_percentage" : float(10),
    "risk_type" : str("balance_percentage") # flat #martingale #compound_all #compund_profit_only #balance_percentage 
} 
account_type    = "PRACTICE" # / REAL / PRACTICE /TOURNAMENT /TOURNAMENT APRIL TOURNAMENT/ IQ LAUNCH /RAMADAN
stake           = float(1)
expiration      = int(1)
overbought      = int(73)
oversold        = int(27)
timeframe       = int(5)

trade = RsiStrategy(risk_management, stake, expiration,account_type)   

symbols = ["EURUSD-OTC","EURJPY-OTC","EURGBP-OTC","GBPUSD-OTC","GBPJPY-OTC","USDJPY-OTC","USDCHF-OTC","USDZAR-OTC","NZDUSD-OTC","USDXOF","USDSGD-OTC"]

for symbol in symbols:
    multiprocessing.Process(target=trade.start, args = (symbol,"digital",overbought,oversold,timeframe)).start()


