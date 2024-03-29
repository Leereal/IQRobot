
import json
import sys
import time
import numpy
from playsound import playsound
from    iqoptionapi.stable_api import IQ_Option
import multiprocessing
from talib.abstract import *

total_profit = 0
curr_balance = 0
payout = 0.95

def start(account_type, risk_management, expiration, stake, symbol, timeframe,current_level,martingale_stake,lock,open_trade):

    email = "jaeljayleen@gmail.com"
    password = "2018$1952"

    # email = "agukamba@outlook.com"
    # password = "ratinati12"

    API = IQ_Option(email, password)

    if API.check_connect() == False:
        if API.connect():
            print(
                f"IQOption API Version: {API.__version__} Connected Successfully")
            playsound('Audios/login.mp3')
        else:
            print(
                "Oops connection failed. Use correct details or check internet connection")
    else:
        pass

    # #Switch accounts you want to trade
    API.change_balance(account_type)

    # Initialize Variables
    balance = API.get_balance()
    daily_risk = risk_management['maximum_risk_']
    daily_target = risk_management['maximum_risk_target']
    risk_type = risk_management['risk_type']
    risk_percentage = risk_management['risk_percentage']
    stake_percentage = risk_management['stake_percentage']

    global curr_balance
    curr_balance = balance

    # print(API.get_profile_ansyc()["balances"]) #To check tournament IDs
    

    print(f"Account Type: {account_type} | Account Balance : {balance}")

    #+|================================ FUNCTIONS TO ENTER A TRADE =========================|+#

    def calculateStake():
        """Calculate amount size to use on each trade"""
        # flat #martingale #compound_all #compund_profit_only #balance_percentage
        account_balance = API.get_balance()
        if account_balance < 1:
            sys.exit()      
       

        # Check if account is not going to loss below target
        if risk_percentage != 0:
            global curr_balance
            if account_balance > curr_balance:
                curr_balance = account_balance
                print(curr_balance)

            elif account_balance < curr_balance and account_balance <= (((100-risk_percentage)/100)*curr_balance):
                print(
                    f"We are now losing {risk_percentage}% below of the amount we made or invested")

                playsound("Audios/entry_fail.mp3")
                sys.exit()

        if account_balance >= daily_target:
            print("Target reached")
            playsound("Audios/entry_fail.mp3")
            sys.exit()

        elif account_balance <= daily_risk:
            print("Loss reached")
            playsound("Audios/entry_fail.mp3")
            sys.exit()

        if risk_type == 'flat':
            return stake

        elif risk_type == 'balance_percentage':
            balance_percentage_amount = round(
                (stake_percentage / 100 * account_balance), 2)
            print(
                f"Balance Percentage Risk Type : {balance_percentage_amount}")
            if balance_percentage_amount > 20000:
                return 20000
            elif balance_percentage_amount < 1:
                return 1
            else:
                return balance_percentage_amount

        elif risk_type == 'compound_all':
            all = round(account_balance, 2)
            print(f"All In Risk Type : {all}")
            return all
        
        elif risk_type     == 'martingale':
            if current_level.value == 1:
                with lock:
                    martingale_stake.value = round((0.0154*account_balance),2)           
                return martingale_stake.value
            
            #Calculate martingale here
            else:
                totalLastStakes = 0
                new_stake = 0           
                i = 1
                while i <= current_level.value:     
                    new_stake = (martingale_stake.value * i * payout + totalLastStakes) / payout
                    totalLastStakes = totalLastStakes + new_stake
                    i += 1                

                print("Martingale Stake: ",round(new_stake,2))
                return round(new_stake,2)


    def openPositions():
        """Return number of open positions"""

        # binary = API.get_positions("turbo-option")[1]['total'] /# Not woriking
        digital = API.get_positions("digital-option")[1]['total']

        return digital

    def trade(symbol, action, option):
        """Execute Trade for digital"""

        start_time = time.time()  # Execution starting time

        # Local Variables to use
        open_positions = openPositions()
        stake = calculateStake()

        # Check if there are running trades first
        if open_positions > 0:
            print("Trade failed because there is a running position.")

        elif open_positions == 0:

            # Entry Success notification
            def successEntryNotification(id, end_time):
                print(
                    f"ID: {id} Symbol: {symbol} - {action.title()} Order executed successfully")
                print(
                    f"Execution Time : {round((end_time-start_time),3)} secs")
                playsound('Audios/entry.mp3')

            # Entry Fail notification
            def failedEntryNotification():
                print(
                    "{symbol} Failed to execute maybe your balance low or asset is closed")
                playsound("Audios/entry_fail.mp3")
                with lock:
                        open_trade.value = False
                time.sleep(60*2)

            print(f"Open Value is . {open_trade.value} ")  
            # DIGITAL TRADING
            if option == "digital" and open_trade.value == False:
                with lock:
                    open_trade.value = True   
                    check, id = API.buy_digital_spot(
                        symbol, stake, action, expiration)  # Enter
                    end_time = time.time()  # Execution finishing time                

                if check == True:                 
                    successEntryNotification(id, end_time)
                    # Currently only for digital available
                    watchTrade(id, symbol, stake)
                else:
                    failedEntryNotification()

            # BINARY TRADING
            elif option == "binary" and open_trade.value == False:
                with lock:
                    open_trade.value = True                
                    check, id = API.buy(stake, symbol, action, expiration)  # Enter
                    end_time = time.time()  # Execution finishing time
            

                if check == True:
                    successEntryNotification(id, end_time)
                else:
                    failedEntryNotification()
                    with lock:
                        open_trade.value = False                  
            else:
                print(f"Open Value is True. {symbol} not executable")                

    def watchTrade(id, symbol, stake):
        """"Monitoring Opened position"""

        while True:
            check, win = API.check_win_digital_v2(id)
            if check == True:
                break

        if win < 0:
            global total_profit     
            with lock:
                current_level.value += 1          

            # Lose Notification
            total_profit = round((total_profit - stake), 2)
            win_result = f"\n{symbol} Won Profit is now $0 and loss -${stake}  => Total Profit = ${round(total_profit, 2)}"
            with open('trade_results.txt', 'a') as f:
                f.write(win_result)
            print(f"{symbol} Lost")
            playsound('Audios/fail.mp3')
            time.sleep(60*3)
            with lock:
                open_trade.value = False           

        else:
            with lock:
                current_level.value = 1         
            # Win Notification
            total_profit += round(win, 2)
            win_result = f"\n{symbol} Won Profit is now ${round(win,2)} and loss $0 => Total Profit = ${total_profit}"
            with open('trade_results.txt', 'a') as f:
                f.write(win_result)
            print(f"{symbol} Won")
            playsound('Audios/success.mp3')
            time.sleep(60)
            with lock:
                open_trade.value = False          

    #+|========================CANDLES FUNCTIONS=========================|+#
    def getClosePrices(symbol, timeframe):
        """Get live close prices array only. Returns array of close prices"""

        candles = API.get_realtime_candles(symbol, int(timeframe))

        data = []
        for x in list(candles):
            data.append(candles[x]['close'])

        close = numpy.array(data)
        return close

    def getData(candles):
        """Get live open,close,high,low prices in array form"""

        data = {'open': numpy.array([]), 'high': numpy.array([]), 'low': numpy.array(
            []), 'close': numpy.array([]), 'volume': numpy.array([])}
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

    print(
        f"|+|====================RSI Strategy started on {symbol}==================|+|")

    API.start_candles_stream(symbol, int(timeframe), maxdict)

    while True:

        try:
            rsi_value = RSI(getClosePrices(symbol, timeframe),
                            timeperiod=14)[-1]  # Get the last RSI value

        except KeyError:
            pass

        else:
            print(f"SYMBOL : {symbol} | RSI :  {round(rsi_value, 2)} | Current Level: {current_level.value} | Current Martingale: {martingale_stake.value} | Open Trade: {open_trade.value}")



            # RSI Check
            if rsi_value >= overbought:
                trade(symbol, "put", option)

            elif rsi_value <= oversold:
                trade(symbol, "call", option)


if __name__ == '__main__':
    risk_management = {
        # Balance you want to reach due to profit
        "maximum_risk_target": float(1000000),
        "maximum_risk_": float(0),  # Balance you want to reach due to loss
        "stake_percentage": float(20),
        # flat #martingale #compound_all #compund_profit_only #balance_percentage
        "risk_type": str("martingale"),
        "risk_percentage": float(0),
    }
    # / REAL / PRACTICE /TOURNAMENT /TOURNAMENT APRIL TOURNAMENT/ IQ LAUNCH /RAMADAN
    account_type = "PRACTICE"
    stake = float(5000)
    expiration = int(1)
    overbought = int(70)
    oversold = int(30)
    timeframe = int(5)
    option = "digital"
    current_level = multiprocessing.Value('i',1)
    martingale_stake = multiprocessing.Value('d',1.0)
    open_trade = multiprocessing.Value('i',False)
    lock = multiprocessing.Lock()

    # start(account_type, risk_management, expiration,
    #       stake, "EURUSD-OTC", timeframe)
    # start(account_type,risk_management,expiration,stake,"EURJPY-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"EURGBP-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"GBPJPY-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"GBPUSD-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"USDJPY-OTC",timeframe)
    # start(account_type,risk_management,expiration,stake,"USDCHF-OTC",timeframe)

    # symbols = ["EURUSD-OTC","EURJPY-OTC","EURGBP-OTC","GBPUSD-OTC","GBPJPY-OTC","USDJPY-OTC","USDCHF-OTC","USDZAR-OTC","NZDUSD-OTC","USDXOF-OTC","USDSGD-OTC"]
    symbols = ["EURUSD","EURJPY","EURGBP","GBPUSD","GBPJPY","USDJPY","USDCAD","AUDUSD"]
    # symbols = ["EURUSD", "EURGBP","EURJPY"]
    # symbols = ["EURUSD"]

    for symbol in symbols:
        multiprocessing.Process(target=start, args=(
            account_type, risk_management, expiration, stake, symbol, timeframe,current_level ,martingale_stake,lock,open_trade)).start()
    

