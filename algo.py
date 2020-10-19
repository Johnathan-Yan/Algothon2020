import yfinance as yf
import datetime
import math
import time

portfolio = {'Money': 1000000}
market_cap_history = {'MSFT' : 1660000000000, 'AMZN' : 1639000000000, 'AAPL' : 2036000000000, 'GOOG' : 1070000000000,
                      'NVDA' : 341260000000, 'CRM' : 235280000000}
stock_codes = ['MSFT', 'AMZN', 'AAPL', 'GOOG', 'NVDA', 'CRM']
history_dict = {}
sales = {'Buy': 0, 'Sell': 0}

def grab_history(trade_start, trade_end):
    for ticker in stock_codes:
        history_dict[ticker] = yf.Ticker(ticker).history(start=trade_start, end=trade_end).Close

def algo(dt):
    if dt not in history_dict[stock_codes[0]]:
        print(" ------ ")
        print('Can not trade today.')
        return

    start_dt = dt - datetime.timedelta(31)
    total_capped_mean = 0
    total_market_cap = 0
    weighted_variance = 0
    datelist = []

    for i in range(0, 31):
        datelist.append(start_dt + datetime.timedelta(days=i))

    for ticker in stock_codes:
        total_pct_change = 0
        count = 0
        prev = -1

        for day in datelist:
            if day in history_dict[ticker]:
                stock_price = history_dict[ticker][day]
                if prev == -1:
                    prev = stock_price
                    continue
                total_pct_change += abs((stock_price / prev) - 1)
                count += 1
                prev = stock_price
            else:
                continue
        mean = total_pct_change / count
        market_cap = market_cap_history[ticker]
        capped_mean = mean * market_cap
        total_capped_mean += capped_mean
        total_market_cap += market_cap

    weighted_mean = total_capped_mean / total_market_cap

    for ticker in stock_codes:
        count = 0
        prev = -1
        total_variance = 0
        for day in datelist:
            if day in history_dict[ticker]:
                stock_price = history_dict[ticker][day]
                if prev == -1:
                    prev = stock_price
                    continue
                current_pct_change = abs((stock_price / prev) - 1)
                total_variance += (current_pct_change - weighted_mean) ** 2
                count += 1
                prev = stock_price
            else:
                continue
        mean = total_variance / count
        market_cap = market_cap_history[ticker]
        weighted_variance += mean * market_cap

    weighted_std_deviation = math.sqrt(weighted_variance / total_market_cap)
    max_daily_change = 0
    moveable_units = {}
    best_ticker = None

    for ticker in stock_codes:
        for i in range(1, 10):
            if dt - datetime.timedelta(days=i) in history_dict[ticker]:
                dt_prev = dt - datetime.timedelta(days=i)
                break

        today_price = history_dict[ticker][dt]
        prev_price = history_dict[ticker][dt_prev]
        daily_change = (today_price / prev_price) - 1
        deviations_changed = (daily_change - weighted_mean) / weighted_std_deviation

        if not ticker in portfolio:
            portfolio[ticker] = 0

        if deviations_changed > 0:
            if portfolio[ticker] < math.floor(((abs(deviations_changed) ** 2) * 5000) / today_price):
                moveable_units[ticker] = -(portfolio[ticker])
            else:
                moveable_units[ticker] = -math.floor((((abs(deviations_changed) ** 2) * 5000) / today_price))
        else:
            if portfolio['Money'] < math.floor(((abs(deviations_changed) ** 2) * 5000)):
                moveable_units[ticker] = math.floor(portfolio['Money'] / today_price)
            else:
                moveable_units[ticker] = math.floor(((abs(deviations_changed) ** 2) * 5000) / today_price)

        if moveable_units[ticker] != 0:
            if deviations_changed >= -2 and abs(deviations_changed) > 1:
                if abs(moveable_units[ticker] * today_price) > max_daily_change:
                    max_daily_change = moveable_units[ticker] * today_price
                    best_ticker = ticker
                    best_today_price = today_price

    print(" ------ ")
    if best_ticker == None:
        print("No buying on this day")
        return

    print("date: " + dt.strftime('%Y-%m-%d'))
    print("maximum moveable units: " + str(moveable_units[best_ticker]))
    print("best ticker to buy/sell: " + str(best_ticker))

    if moveable_units[best_ticker] != 0:
        portfolio['Money'] -= history_dict[best_ticker][dt] * moveable_units[best_ticker]
        portfolio[best_ticker] += moveable_units[best_ticker]

        if moveable_units[best_ticker] > 0:
            sales['Buy'] += 1
        elif moveable_units[best_ticker] < 0:
            sales['Sell'] += 1

        print("spending: " + str(moveable_units[best_ticker] * history_dict[best_ticker][dt]))
        print("current money: " + str(portfolio['Money']))
        print("price today: " + str(best_today_price))

    return

trade_start_date = datetime.datetime(2017, 1, 1)
numdays = 1368

grab_history(trade_start_date - datetime.timedelta(days=31), trade_start_date + datetime.timedelta(days=numdays))

trade_datelist = []
for x in range (0, numdays):
    trade_datelist.append(trade_start_date + datetime.timedelta(days = x))

for date in trade_datelist:
    algo(date)

portfolio['Wealth'] = 0

print("-----  Results  -----")

for stock in portfolio:
    if stock != 'Money':
        if stock != 'Wealth':
            current_price = history_dict[stock][-1]
            portfolio['Wealth'] += current_price * portfolio[stock]
            print("Holding " + str(stock))
            print("Units : " + str(portfolio[stock]))
            print("Value : " + str(current_price * portfolio[stock]))
    elif stock == 'Money':
        portfolio['Wealth'] += portfolio[stock]
        print("Holding " + str(portfolio[stock]), end = ' ')
        print("in cash")

print("Total wealth at trading end is: " + str(portfolio['Wealth']))
print("Traded since " + trade_start_date.strftime('%Y-%m-%d') + " for " + str(numdays) + " days")
print("Total buys: " + str(sales['Buy']))
print("Total sells: " + str(sales['Sell']))