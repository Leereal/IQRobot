
import json
import sys
import time
import numpy
from playsound import playsound
from iqoptionapi.stable_api import IQ_Option
import multiprocessing
from talib.abstract import *

total_profit = 0
curr_balance = 0


def start(account_type,risk_management,expiration,stake,symbol,timeframe):

    email = "jaeljayleen@gmail.com"
    password = "2018$1952"

    # email = "agukamba@outlook.com"
    # password = "ratinati12"

    API = IQ_Option(email,password)

    if API.check_connect()==False:
        if(API.connect()):
            print(f"IQOption API Version: {API.__version__} Connected Successfully")
            playsound('Audios/login.mp3')
        else:
            print("Oops connection failed. Use correct details or check internet connection")
    else:
        pass
        
    # #Switch accounts you want to trade         
    API.change_balance(account_type)

    #Initialize Variables
    balance            = API.get_balance()
    daily_risk         = risk_management['maximum_risk_']
    daily_target       = risk_management['maximum_risk_target']  
    risk_type          = risk_management['risk_type']
    risk_percentage    = risk_management['risk_percentage'] 
    stake_percentage   = risk_management['stake_percentage'] 

    global curr_balance
    curr_balance = balance

    #print(API.get_profile_ansyc()["balances"]) To check tournament IDs

    #Print Balance
    print(f"Account Type: {account_type} | Account Balance : {balance}")

    #+|================================ FUNCTIONS TO ENTER A TRADE =========================|+#
    def calculateStake():
        """Calculate amount size to use on each trade"""
        # flat #martingale #compound_all #compund_profit_only #balance_percentage
        account_balance = API.get_balance()
        if account_balance < 1:
            sys.exit()

        #Check if account is not going to loss below target
        if risk_percentage != 0 :
            global curr_balance
            if account_balance > curr_balance:
                curr_balance = account_balance
                print(curr_balance)

            elif account_balance < curr_balance and account_balance <= (((100-risk_percentage)/100)*curr_balance):
                print(f"We are now losing {risk_percentage}% below of the amount we made or invested")

                playsound("Audios/entry_fail.mp3")
                sys.exit()
                    
        if account_balance >= daily_target :
            print("Target reached")
            playsound("Audios/entry_fail.mp3")
            sys.exit()

        elif account_balance <= daily_risk :
            print("Loss reached") 
            playsound("Audios/entry_fail.mp3")
            sys.exit()

        if risk_type       == 'flat':
            return stake

        elif risk_type     == 'balance_percentage':            
            balance_percentage_amount = round((stake_percentage / 100 * account_balance), 2 )
            print (f"Balance Percentage Risk Type : {balance_percentage_amount}")
            if balance_percentage_amount > 20000:
                return 20000
            elif balance_percentage_amount < 1:
                return 1
            else:
                return balance_percentage_amount 

        elif risk_type     == 'compound_all':
            all = round(account_balance,2)
            print (f"All In Risk Type : {all}")
            return all


    def openPositions():
        """Return number of open positions"""

        # binary = API.get_positions("turbo-option")[1]['total'] /# Not woriking
        digital = API.get_positions("digital-option")[1]['total']

        return digital 

    
    def trade(symbol,action,option):
        """Execute Trade for digital"""        

        start_time = time.time() # Execution starting time

        #Local Variables to use
        open_positions  = openPositions()
        stake           = calculateStake()
    
        #Check if there are running trades first
        if open_positions > 0 :
            print("Trade failed because there is a running position.")

        elif open_positions == 0:
            
            #Entry Success notification
            def successEntryNotification(id,end_time):
                print(f"ID: {id} Symbol: {symbol} - {action.title()} Order executed successfully")
                print(f"Execution Time : {round((end_time-start_time),3)} secs")
                playsound('Audios/entry.mp3')

            #Entry Fail notification
            def failedEntryNotification():
                print("{symbol} Failed to execute maybe your balance low or asset is closed")
                playsound("Audios/entry_fail.mp3")
                time.sleep(60*4)

            #DIGITAL TRADING
            if option == "digital" :
                check,id = API.buy_digital_spot(symbol,stake,action,expiration) # Enter
                end_time = time.time() # Execution finishing time

                if check == True :
                    successEntryNotification(id,end_time)
                    watchTrade(id,symbol,stake) #Currently only for digital available
                else:
                    failedEntryNotification()                

            #BINARY TRADING
            elif option == "binary" :
                check,id = API.buy(stake,symbol,action,expiration) # Enter
                end_time = time.time() # Execution finishing time

                if check == True :
                    successEntryNotification(id,end_time)                    
                else:
                    failedEntryNotification()
    

    def watchTrade(id,symbol,stake):
        """"Monitoring Opened position"""

        while True:
            check,win = API.check_win_digital_v2(id)
            if check == True:                  
                break               

        if win < 0:
            global total_profit

            #Lose Notification
            total_profit = round((total_profit - stake),2)
            win_result = f"\n{symbol} Won Profit is now $0 and loss -${stake}  => Total Profit = ${round(total_profit, 2)}"
            with open('trade_results.txt','a') as f:                     
                f.write(win_result)                
            print(f"{symbol} Lost")
            playsound('Audios/fail.mp3')

        else: 
            #Win Notification                   
            total_profit += round(win,2)
            win_result = f"\n{symbol} Won Profit is now ${round(win,2)} and loss $0 => Total Profit = ${total_profit}"
            with open('trade_results.txt','a') as f:                       
                f.write(win_result)
            print(f"{symbol} Won")
            playsound('Audios/success.mp3')     

        time.sleep(60*3)  
    

    #+|========================CANDLES FUNCTIONS=========================|+#
    def getClosePrices(candles):
        """Get live close prices array only. Returns array of close prices"""
        data = [] 
        for x in list(candles):
            data.append(candles[x]['close'])

        close = numpy.array(data)
        return close
    
    def getData(candles):
        """Get live open,close,high,low prices in array form"""	

        data = {'open': numpy.array([]), 'high': numpy.array([]), 'low': numpy.array([]), 'close': numpy.array([]), 'volume': numpy.array([]) }
        for x in list(candles):
            data['open'] = numpy.append(data['open'], candles[x]['open'])
            data['high'] = numpy.append(data['open'], candles[x]['max'])
            data['low'] = numpy.append(data['open'], candles[x]['min'])
            data['close'] = numpy.append(data['open'], candles[x]['close'])
            data['volume'] = numpy.append(data['open'], candles[x]['volume'])
        return data

# +|========================STRATEGY BEGIN=========================|+#

    """Place a trade based on RSI rules"""      
    maxdict = 280

    print(f"|+|====================RSI Strategy started on {symbol}==================|+|")

    API.start_candles_stream(symbol,int(timeframe),maxdict)
    candles = API.get_realtime_candles(symbol, int(timeframe))

    API.start_candles_stream(symbol,int(60),maxdict)
    candles2 = API.get_realtime_candles(symbol, int(60))

    while True:

        try:            
            rsi_value = RSI(getClosePrices(candles), timeperiod=14)[-1] #Get the last RSI value
            upperband, middleband, lowerband = BBANDS(getClosePrices(candles2)*100000, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0) 
            bb_hi = upperband[-1]/100000
            bb_lw = lowerband[-1]/100000
            curr_price = getClosePrices(candles)[-1]

        except KeyError:
            pass

        else:
            print(f"SYMBOL : {symbol} | RSI :  {round(rsi_value, 2)} | BB UPPER = {bb_hi} | BB LOWER =  {bb_lw} | PRICE = {curr_price}") 

            # #RSI Check               
            if rsi_value >= overbought and curr_price > bb_hi :
                trade(symbol,"put",option)

            elif rsi_value <= oversold and curr_price < bb_lw : 
                trade(symbol,"call",option)
    


if __name__ == '__main__':
    risk_management = {
    "maximum_risk_target":float(100000), #Balance you want to reach due to profit
    "maximum_risk_":float(0),# Balance you want to reach due to loss
    "stake_percentage" : float(10),
    "risk_type" : str("flat"), # flat #martingale #compound_all #compund_profit_only #balance_percentage 
    "risk_percentage" : float(0),
    } 
    account_type    = "TOURNAMENT" # / REAL / PRACTICE /TOURNAMENT /TOURNAMENT APRIL TOURNAMENT/ IQ LAUNCH /RAMADAN
    stake           = float(100)
    expiration      = int(1)
    overbought      = int(77)
    oversold        = int(23)
    timeframe       = int(5)
    option          = "digital" 

    # start(account_type,risk_management,expiration,stake,"EURUSD",timeframe)
    # start(account_type,risk_management,expiration,stake,"EURJPY-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"EURGBP",timeframe)
    # start(account_type,risk_management,expiration,stake,"GBPJPY-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"GBPUSD-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"EURJPY",timeframe)
    # start(account_type,risk_management,expiration,stake,"USDCHF-OTC",timeframe)

    # symbols = ["EURUSD-OTC","EURJPY-OTC","EURGBP-OTC","GBPUSD-OTC","GBPJPY-OTC","USDJPY-OTC","USDCHF-OTC","USDZAR-OTC","NZDUSD-OTC","USDXOF-OTC","USDSGD-OTC"]
    # symbols = ["EURUSD","EURJPY","EURGBP","GBPJPY","USDJPY","AUDJPY","AUDCAD","USDCAD",]
    symbols = ["EURUSD","EURJPY","EURGBP","GBPUSD","GBPJPY","USDJPY","USDCAD","AUDUSD","AUDJPY","AUDCAD"]
    # symbols = ["EURUSD","EURGBP","EURJPY"]
    # ]

    for symbol in symbols:    
        multiprocessing.Process(target=start, args = (account_type,risk_management,expiration,stake,symbol,timeframe)).start()

