import datetime
import sys
import time
import numpy
from playsound import playsound
from iqoptionapi.stable_api import IQ_Option
import json

#Global Initialization
total_profit = 0

class Trade:
    """All account and trading attributes and methods are here"""

    def __init__(self,risk_management, stake, expiration, account_type) -> None:

        # # Login Variables 
        email = "jaeljayleen@gmail.com"
        password = "tambos@1992" 

        # email = "pipsbulls@gmail.com"
        # password = "mutabvuri$8" 

        # Get login details from json file
        # file_name = "user.json"
        # try:
        #     with open(file_name,"r") as f:
        #         user = json.load(f)
        # except FileNotFoundError:
        #     print("File with login details is not found. Please create one")
        # else:
        #     email =  user[0]
        #     password = user[1]       
    
        #Connection to IQOption
        self.API = IQ_Option(email,password)

        if self.API.check_connect()==False:
            if(self.API.connect()):
                print(f"IQOption API Version: {self.API.__version__} Connected Successfully")
                playsound('Audios/login.mp3')
            else:
                print("Oops connection failed. Use correct details or check internet connection")
        else:
            pass
        
        # #Switch accounts you want to trade         
        self.API.change_balance(account_type)

        #Initialize Variables
        self.balance            = self.API.get_balance()
        self.daily_risk         = risk_management['maximum_risk_']
        self.daily_target       = risk_management['maximum_risk_target']
        self.expiration         = expiration
        self.risk_type          = risk_management['risk_type']
        self.risk_type          = risk_management['risk_type']
        self.stake              = stake
        self.stake_percentage   = risk_management['stake_percentage']        

        #Print Balance
        print(f"Account Type: {account_type} | Account Balance : {self.balance}")

#+|================================ FUNCTIONS TO ENTER A TRADE =========================|+#
    def calculateStake(self):
        """Calculate amount size to use on each trade"""
        # flat #martingale #compound_all #compund_profit_only #balance_percentage

        stake = self.stake
        account_balance = self.API.get_balance()
        
        if account_balance >= self.daily_target :
            print("Target reached")
            sys.exit()
        elif account_balance <= self.daily_risk :
            print("Loss reached") 
            sys.exit()

        if self.risk_type       == 'flat':
            return stake

        elif self.risk_type     == 'balance_percentage':            
            balance_percentage_amount = round((self.stake_percentage / 100 * account_balance), 2 )
            print (f"Balance Percentage Risk Type : {balance_percentage_amount}")
            return balance_percentage_amount 

        elif self.risk_type     == 'compound_all':
            all = round(account_balance,2)
            print (f"All In Risk Type : {all}")
            return all 

    def trade(self,symbol,action,option):
        """Execute Trade for digital"""        

        start_time = time.time() # Execution starting time

        #Local Variables to use
        open_positions  = self.openPositions()
        stake           = self.calculateStake()
        expiration      = self.expiration
    
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
                check,id = self.API.buy_digital_spot(symbol,stake,action,expiration) # Enter
                end_time = time.time() # Execution finishing time

                if check == True :
                    successEntryNotification(id,end_time)
                    self.watchTrade(id,symbol,stake) #Currently only for digital available
                else:
                    failedEntryNotification()                

            #BINARY TRADING
            elif option == "binary" :
                check,id = self.API.buy(stake,symbol,action,expiration) # Enter
                end_time = time.time() # Execution finishing time

                if check == True :
                    successEntryNotification(id,end_time)                    
                else:
                    failedEntryNotification()
 
    def openPositions(self):
        """Return number of open positions"""

        # binary = self.API.get_positions("turbo-option")[1]['total'] /# Not woriking
        digital = self.API.get_positions("digital-option")[1]['total']

        return digital
    
    def watchTrade(self,id,symbol,stake):
        """"Monitoring Opened position"""

        while True:
            check,win = self.API.check_win_digital_v2(id)
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

    def api(self):
        """Public API connector"""
        return self.API

#+|========================CANDLES FUNCTIONS=========================|+#
    def getClosePrices(self,symbol,timeframe):
        """Get live close prices array only. Returns array of close prices"""

        candles = self.API.get_realtime_candles(symbol, int(timeframe))
    
        data = [] 
        for x in list(candles):
            data.append(candles[x]['close'])

        close = numpy.array(data)
        return close

    def getData(self, candles):
        """Get live open,close,high,low prices in array form"""	

        data = {'open': numpy.array([]), 'high': numpy.array([]), 'low': numpy.array([]), 'close': numpy.array([]), 'volume': numpy.array([]) }
        for x in list(candles):
            data['open'] = numpy.append(data['open'], candles[x]['open'])
            data['high'] = numpy.append(data['open'], candles[x]['max'])
            data['low'] = numpy.append(data['open'], candles[x]['min'])
            data['close'] = numpy.append(data['open'], candles[x]['close'])
            data['volume'] = numpy.append(data['open'], candles[x]['volume'])
        return data

        
















