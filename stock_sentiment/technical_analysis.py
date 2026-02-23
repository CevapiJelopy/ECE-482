import yfinance as yf
import pandas as pd
from massive import RESTClient
from datetime import datetime, timedelta

client = RESTClient("BjANqHq6MYW9FUD6r1IKsx81tHLY6m9l")

end = datetime.today()
start = end - timedelta(days=120)
ticker = 'AAPL'

aggs = client.get_aggs(
    ticker=ticker,
    multiplier=1,
    timespan="day",
    from_=start.strftime("%Y-%m-%d"),
    to=end.strftime("%Y-%m-%d"),
)



data = pd.DataFrame(aggs)

data['timestamp'] = pd.to_datetime(data["timestamp"], unit="ms")
data['volume'] = data['volume'].astype(int)
data['open'] = data['open'].round(2)
data.set_index("timestamp", inplace=True)

##ticker = yf.Ticker("AAPL")
##data = ticker.history(period='6mo') #period must be longer than 3 months to properly calculate 100EMA


# -----------------EMA-------------------------------------------------------------------------------


def calculate_EMA(data):
    data['EMA100'] = data['close'].ewm(span=100, adjust=False).mean().round(3)
    data['EMA50'] = data['close'].ewm(span=50, adjust=False).mean().round(3)
    data['EMA25'] = data['close'].ewm(span=25, adjust=False).mean().round(3)

def is_ema100_uptrend(data, period):
    ema100 = data['EMA100']
    # Check if the EMA100 has been on an uptrend for the past period=# days
    if ema100.iloc[-1] > ema100.iloc[-period:].min():
        return 1
    else:
        return 0
    
# after testing, you can try adding points for "is_ema50_uptrend" and "is_ema25_uptrend"
# BUT if ema25 and ema50 are already above ema100, adding points for being on an uptrend would
# not add new value since those two emas being above 100 already means theyre on an uptrend

def is_ema50_above_ema100(data, period):
    ema50 = data['EMA50']
    ema100 = data['EMA100']
    # Check if EMA50 has been above EMA100 the past period=# days
    if all(ema50.iloc[-period:] > ema100.iloc[-period:]):
        return 1
    else:
        return 0
    
def is_ema25_above_ema100(data, period):
    ema25 = data['EMA25']
    ema100 = data['EMA100']
    # Check if EMA25 has been above EMA100 the past period=# days
    if all(ema25.iloc[-period:] > ema100.iloc[-period:]):
        return 1
    else:
        return 0
    
    
# could add points for EMA range difference, IE, if ema25 is WAY above ema100, this is a bullish signal
# and can be weighted to hold more importance.
# you could calulcate recent EMA range averages and add points if a short term EMA is above the standard deviation

# Weights can be changed during testing
    
def calculate_EMA_points(data, period):
    points = 0
    trend = 0

    if (is_ema100_uptrend(data, period)):
        points +=1
        trend = 1
    else: 
        points -=1
        trend = 0
        
    if (is_ema50_above_ema100(data,period)):
        points +=1
    else:
        if (trend == 0):
            points -=1
        
    if (is_ema25_above_ema100(data,period)):
        points +=2
    else:
        if (trend == 0):
            points -=2

    # print EMA conditions 
    print('EMA100 on an uptrend:')
    print(is_ema100_uptrend(data,period))
    
    print('EMA50 above EMA100:')
    print(is_ema50_above_ema100(data,period))

    print('EMA25 above EMA100:')
    print(is_ema25_above_ema100(data,period))
    return points


# ---------------------------------------------------------------------------------------------------

# -----RSI-------------------------------------------------------------------------------------------

rsi14 = client.get_rsi(
    ticker=ticker,
	timespan="day",
	adjusted="true",
	window="14",
	series_type="close",
	order="desc",
	limit="10",
)

rsi50 = client.get_rsi(
    ticker=ticker,
	timespan="day",
	adjusted="true",
	window="50",
	series_type="close",
	order="desc",
	limit="10",
)

rsi14_data = pd.DataFrame([v.__dict__ for v in rsi14.values])
rsi50_data = pd.DataFrame([v.__dict__ for v in rsi50.values])

rsi14_data["timestamp"] = pd.to_datetime(rsi14_data["timestamp"], unit="ms")
rsi14_data.set_index("timestamp", inplace=True)
rsi50_data["timestamp"] = pd.to_datetime(rsi50_data["timestamp"], unit="ms")
rsi50_data.set_index("timestamp", inplace=True)

rsi14_data['value'] = rsi14_data['value'].round(2)
rsi50_data['value'] = rsi50_data['value'].round(2)

rsi14_data = rsi14_data.rename(columns={"value": "RSI14"})
rsi50_data = rsi50_data.rename(columns={"value": "RSI50"})

rsi_combined = rsi14_data.join(rsi50_data, how="inner")  

print(rsi_combined)

def rsi14_signal(rsi14_data):
    # Get the most recent RSI14 value
    latest_rsi14 = rsi14_data['RSI14'].iloc[-1]

    if latest_rsi14 > 60:
        return 1   # bullish confirmation
    elif latest_rsi14 < 40:
        return -1  # bearish warning
    else:
        return 0   # neutral

#----------------------------------------------------------------------------------------------------



def print_data(data):
    print(data[['open', 'close', 'volume', 'EMA100', 'EMA50', 'EMA25', 'RSI14', 'RSI50']])


calculate_EMA(data)
full_data = data.join(rsi_combined, how="inner")  
points = calculate_EMA_points(full_data, 30)
print('points:')
print(points)
print_data(full_data)
