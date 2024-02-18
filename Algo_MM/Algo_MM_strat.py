'''
Login Details:
    Port: 16570
    Username: BOSU-1
    PW: KAZG
    

'''



import signal
import requests
from time import sleep
import pandas as pd
import numpy as np

# class that passes error message, ends the program
class ApiException(Exception):
    pass

# code that lets us shut down if CTRL C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True
    
API_KEY = {'X-API-Key': 'JZ8B1C7V'} #<- Go to your own RIT and click onto the API button to find your own API
shutdown = False
session = requests.Session()
session.headers.update(API_KEY)
    
#code that gets the current tick
def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'] + (case['period'] - 1) * 300
    raise ApiException('fail - cant get tick')

#code that gets the securities via json  
def get_s(session):
    price_act = session.get('http://localhost:9999/v1/securities')
    if price_act.ok:
        prices = price_act.json()
        return prices
    raise ApiException('fail - cant get securities')    
    
def get_history(session, security):
    resp = session.get('http://localhost:9999/v1/securities/history?ticker=' + security)
    if resp.ok:
        prices = resp.json()
        return prices
    
    
def ticker_bid_ask(session, ticker):
    payload = {'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        return book['bids'][0]['price'], book['asks'][0]['price']
    raise ApiException('Authorization error. Please check API key.')
    
    
def pair_trade(session, ticker1, ticker2):
    ticker_1_bid, ticker_1_ask = ticker_bid_ask(session, ticker1)
    ticker_2_bid, ticker_2_ask = ticker_bid_ask(session, ticker2)
    
    i = 1
    
    if i * ticker_1_bid > ticker_2_ask:
        session.post('http://localhost:9999/v1/orders', params = {'ticker': ticker2, 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
        session.post('http://localhost:9999/v1/orders', params = {'ticker': ticker1, 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
        print('bought ' + ticker2)
        sleep(1)   
        
    if ticker_2_bid > 2.45 * ticker_1_ask:
        session.post('http://localhost:9999/v1/orders', params = {'ticker': ticker1, 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
        session.post('http://localhost:9999/v1/orders', params = {'ticker': ticker2, 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
        print('bought ' + ticker1)
        sleep(1)
    
def main():
    with requests.Session() as session:
        session.headers.update(API_KEY)
        #tick = get_tick(session)
        pd.set_option('chained_assignment',None)
        while get_tick(session) > 0 and get_tick(session) < 298 and not shutdown:
            
            #assets = pd.DataFrame(get_s(session))
            #assets2 = assets.drop(columns=['vwap', 'nlv', 'bid_size', 'ask_size', 'volume', 'realized', 'unrealized', 'currency', 
            #                               'total_volume', 'limits', 'is_tradeable', 'is_shortable', 'interest_rate', 'start_period', 'stop_period', 'unit_multiplier', 
            #                               'description', 'unit_multiplier', 'display_unit', 'min_price', 'max_price', 'start_price', 'quoted_decimals', 'trading_fee', 'limit_order_rebate',
            #                               'min_trade_size', 'max_trade_size', 'required_tickers', 'underlying_tickers', 'bond_coupon', 'interest_payments_per_period', 'base_security', 'fixing_ticker',
            #                               'api_orders_per_second', 'execution_delay_ms', 'interest_rate_ticker', 'otc_price_range'])
            #for row in assets2.index.values:
            #    if 'P' in assets2['ticker'].iloc[row]:
            #        assets2['type'].iloc[row] = 'PUT'
            #    elif 'C' in assets2['ticker'].iloc[row]:
            #        assets2['type'].iloc[row] = 'CALL'
                
            
            #print(assets2.to_markdown(), end='\n'*2)
            #print(get_tick(session))
            

            usd_b, usd_a = ticker_bid_ask(session, 'USD')
            cad_b, cad_a = ticker_bid_ask(session, 'CAD')
            hawk_b, hawk_a = ticker_bid_ask(session, 'HAWK')
            dove_b, dove_a = ticker_bid_ask(session, 'DOVE')
            rit_c_b, rit_c_a = ticker_bid_ask(session, "RIT_C")
            rit_u_b, rit_u_a = ticker_bid_ask(session, "RIT_U")
            
            
            both_b = hawk_b + dove_b
            both_a = hawk_a + dove_a
            
            coms = 0.06
            sleep_time = 0
            
            if both_b > rit_c_a + coms:
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'RIT_C', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'HAWK', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'DOVE', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                print('bought ETF and sold two stocks')
                sleep(sleep_time)
            if rit_c_b > both_a + coms:
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'RIT_C', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'HAWK', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'DOVE', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                print('bought two stocks and sold ETF')
                sleep(sleep_time)
                
            if both_b > rit_u_a * usd_a + coms:
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'RIT_U', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'USD', 'type': 'MARKET', 'quantity': int(rit_u_a), 'action': 'BUY'})
                
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'HAWK', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'DOVE', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                print('sold two stocks and exchanged for USD to buy US ETF')
                sleep(sleep_time)
            
            if rit_u_b * usd_b > both_a + coms:
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'RIT_U', 'type': 'MARKET', 'quantity': 1000, 'action': 'SELL'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'USD', 'type': 'MARKET', 'quantity': int(both_a), 'action': 'SELL'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'HAWK', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                session.post('http://localhost:9999/v1/orders', params = {'ticker': 'DOVE', 'type': 'MARKET', 'quantity': 1000, 'action': 'BUY'})
                print('sold US ETF and exchanged for CAD to buy two stocks')
                sleep(sleep_time)
            
            #asset = pd.DataFrame(get_history(session, 'USD'))
            #print(assets)
            
            #sleep(1)
if __name__ == '__main__':
        main()