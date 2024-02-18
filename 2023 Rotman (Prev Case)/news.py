
import signal
import requests
from time import sleep
# this class definition allows us to print error messages and stop the program when ne
class ApiException(Exception):
    pass
# this signal handler allows for a graceful shutdown when TRL+C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal. signal(signal.SIGINT, signal.sIG_DFL)
    shutdown = True

API_KEY={'X-API-Key': 'BSGEB9FN'}
shutdown = False
# this helper method returns the current 'tick' of the running case
def get_tick(session):
    resp=session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('Authorization error. Please check API key. ')
# this helper method returns the bid and ask for a given security
def ticker_bid_ask(session, ticker):
    payload ={'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params=payload) 
    if resp.ok:
        book = resp.json()
        return book['bids'][0]['price'], book['asks'][0]['price'] 
    raise ApiException('Authorization error. Please check API key.')

def get_news(session):
    resp=session.get('http://localhost:9999/v1/news')
    if resp.ok:
        news = resp.json()
        return news[1]
    raise ApiException('Authorization error. Please check API key. ')

def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        while tick > 5 and tick < 295 and not shutdown:
             bid, ask =ticker_bid_ask(s,'RTM')
             new=get_news(s)
             print(new.get('body'))

if __name__ == '__main__':
# register the custom signal handler for graceful shutdowns
    signal.signal(signal.SIGINT, signal_handler)
    main()






