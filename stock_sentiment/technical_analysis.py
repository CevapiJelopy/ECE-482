import yfinance as yf

ticker = yf.Ticker("AAPL")
data = ticker.history(period='6mo') #period must be longer than 3 months to properly calculate 100EMA


# -----------------EMA-------------------------------------------------------------------------------


def calculate_EMA(data):
    data['EMA100'] = data['Close'].ewm(span=100, adjust=False).mean().round(3)
    data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean().round(3)
    data['EMA25'] = data['Close'].ewm(span=25, adjust=False).mean().round(3)

def is_ema100_uptrend(data, period):
    ema100 = data['EMA100']
    # Check if the EMA100 has been on an uptrend for the past period=# days
    if ema100[-1] > ema100[-period:].min():
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
    if all(ema50[-period:] > ema100[-period:]):
        return 1
    else:
        return 0
    
def is_ema25_above_ema100(data, period):
    ema25 = data['EMA25']
    ema100 = data['EMA100']
    # Check if EMA25 has been above EMA100 the past period=# days
    if all(ema25[-period:] > ema100[-period:]):
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


#----------------------------------------------------------------------------------------------------



def print_data(data):
    print(data[['Open', 'Close', 'Volume', 'EMA100', 'EMA50', 'EMA25']])


calculate_EMA(data)
points = calculate_EMA_points(data, 30)
print('points:')
print(points)
print_data(data)