import signal
import requests
from time import sleep
import pandas as pd
import matplotlib.pyplot as plt

CAPM_vals = {}
expected_return = {}
# class that passes error message, ends the program
class ApiException(Exception):
    pass

# code that lets us shut down if CTRL C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

API_KEY = {'X-API-Key': 'rotman'}
shutdown = False
session = requests.Session()
session.headers.update(API_KEY)

#code that gets the current tick
def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('fail - cant get tick')

#code that parses the first and latest news instances for forward market predictions and the risk free rate
#Important: this code only works if the only '%' character is in front of the RISK FREE RATE and the onle '$' character is in front of the forward price suggestions
def get_news(session):
    news = session.get('http://localhost:9999/v1/news')    
    if news.ok:
        newsbook = news.json()
        for i in range(len(newsbook[-1]['body'])):
            if newsbook[-1]['body'][i] == '%':
                CAPM_vals['%Rf'] = round(float(newsbook[-1]['body'][i - 4:i])/100, 4)               
        latest_news = newsbook[0]
        if len(newsbook) > 1:
            for j in range(len(latest_news['body']) - 1, 1, -1):    
                while latest_news['body'][j] != '$':
                    j -= 1
            CAPM_vals['forward'] = float(latest_news['body'][j + 1:-1])
        return CAPM_vals
    raise ApiException('timeout')

#gets all the price data for all securities        
def pop_prices(session):
    price_act = session.get('http://localhost:9999/v1/securities')
    if price_act.ok:
        prices = price_act.json()
        return prices
    raise ApiException('fail - cant get securities')
    
#Buy or Sell function, put in your own parameters
def buy_or_sell(session, expected_return):
    for i in expected_return.keys():
        if expected_return[i] > 'ENTER YOUR PARAMETER':
            session.post('http://localhost:9999/v1/orders', params = {'ticker': i, 'type': 'ENTER ORDER TYPE', 'quantity': 'ENTER DESIRED QUANTITY', 'action': 'BUY/SELL'})
        elif expected_return[i] < 'ENTER YOUR PARAMETER':
            session.post('http://localhost:9999/v1/orders', params = {'ticker': i, 'type': 'ENTER ORDER TYPE', 'quantity': 'ENTER DESIRED QUANTITY', 'action': 'BUY/SELL'})

def main():
    with requests.Session() as session:
        session.headers.update(API_KEY)
        ritm = pd.DataFrame(columns= ['RITM','BID', 'ASK', 'LAST', '%Rm'])
        alpha = pd.DataFrame(columns= ['ALPHA','BID', 'ASK', 'LAST', '%Ri', '%Rm'])
        gamma = pd.DataFrame(columns= ['GAMMA','BID', 'ASK', 'LAST', '%Ri', '%Rm'])
        theta = pd.DataFrame(columns= ['THETA','BID', 'ASK', 'LAST', '%Ri', '%Rm'])
        while get_tick(session) < 600 and not shutdown:
            #update the forward market price and rf rate
            get_news(session)
            
            ##update RITM bid-ask dataframe
            pdt_RITM = pd.DataFrame(pop_prices(session)[0])
            ritmp = pd.DataFrame({'RITM': '', 'BID': pdt_RITM['bid'],'ASK': pdt_RITM['ask'], 'LAST': pdt_RITM['last'], '%Rm': ''})
            if ritm['BID'].empty or ritmp['LAST'].iloc[0] != ritm['LAST'].iloc[0]:
                ritm = pd.concat([ritmp, ritm.loc[:]]).reset_index(drop=True)
                ritm['%Rm'] = (ritm['LAST']/ritm['LAST'].shift(-1)) - 1
                if ritm.shape[0] >= 31:
                    ritm = ritm.iloc[:30]
            
            #generate expected market return paramter
            if 'forward' in CAPM_vals.keys():
                CAPM_vals['%RM'] = (CAPM_vals['forward']-ritm['LAST'].iloc[0])/ritm['LAST'].iloc[0]
            else:
                CAPM_vals['%RM'] = ''
                
            
            ##update ALPHA bid-ask dataframe
            pdt_ALPHA = pd.DataFrame(pop_prices(session)[1])
            alphap = pd.DataFrame({'ALPHA': '', 'BID': pdt_ALPHA['bid'],'ASK': pdt_ALPHA['ask'], 'LAST': pdt_ALPHA['last'], '%Ri': '', '%Rm': ''})
            if alpha['BID'].empty or alphap['LAST'].iloc[0] != alpha['LAST'].iloc[0]:
                alpha = pd.concat([alphap, alpha.loc[:]]).reset_index(drop=True)
                alpha['%Ri'] = (alpha['LAST']/alpha['LAST'].shift(-1)) - 1
                alpha['%Rm'] = (ritm['LAST']/ritm['LAST'].shift(-1)) - 1
                if alpha.shape[0] >= 31:
                    alpha = alpha.iloc[:30]
              
            ##update GAMMA bid-ask dataframe
            pdt_GAMMA = pd.DataFrame(pop_prices(session)[2])
            gammap = pd.DataFrame({'GAMMA': '', 'BID': pdt_GAMMA['bid'],'ASK': pdt_GAMMA['ask'], 'LAST': pdt_GAMMA['last'], '%Ri': '', '%Rm': ''})
            if gamma['BID'].empty or gammap['LAST'].iloc[0] != gamma['LAST'].iloc[0]:
                gamma = pd.concat([gammap, gamma.loc[:]]).reset_index(drop=True)
                gamma['%Ri'] = (gamma['LAST']/gamma['LAST'].shift(-1)) - 1
                gamma['%Rm'] = (ritm['LAST']/ritm['LAST'].shift(-1)) - 1
                if gamma.shape[0] >= 31:
                    gamma = gamma.iloc[:30]            
            
            ##update THETA bid-ask dataframe
            pdt_THETA = pd.DataFrame(pop_prices(session)[3])
            thetap = pd.DataFrame({'THETA': '', 'BID': pdt_THETA['bid'],'ASK': pdt_THETA['ask'], 'LAST': pdt_THETA['last'], '%Ri': '', '%Rm': ''})
            if theta['BID'].empty or thetap['LAST'].iloc[0] != theta['LAST'].iloc[0]:     
                theta = pd.concat([thetap, theta.loc[:]]).reset_index(drop=True)
                theta['%Ri'] = (theta['LAST']/theta['LAST'].shift(-1)) - 1
                theta['%Rm'] = (ritm['LAST']/ritm['LAST'].shift(-1)) - 1
                if theta.shape[0] >= 31:
                    theta = theta.iloc[:30]
            
            beta_alpha = (alpha['%Ri'].cov(ritm['%Rm']))/(ritm['%Rm'].var())
            beta_gamma = (gamma['%Ri'].cov(ritm['%Rm']))/(ritm['%Rm'].var())
            beta_theta = (theta['%Ri'].cov(ritm['%Rm']))/(ritm['%Rm'].var()) 
            
            CAPM_vals['Beta - ALPHA'] = beta_alpha
            CAPM_vals['Beta - GAMMA'] = beta_gamma
            CAPM_vals['Beta - THETA'] = beta_theta
            
            if CAPM_vals['%RM'] != '':
                er_alpha = CAPM_vals['%Rf'] + CAPM_vals['Beta - ALPHA'] * (CAPM_vals['%RM'] - CAPM_vals['%Rf'])
                er_gamma = CAPM_vals['%Rf'] + CAPM_vals['Beta - GAMMA'] * (CAPM_vals['%RM'] - CAPM_vals['%Rf'])
                er_theta = CAPM_vals['%Rf'] + CAPM_vals['Beta - THETA'] * (CAPM_vals['%RM'] - CAPM_vals['%Rf'])
            else:
                er_alpha = 'Wait for market forward price'
                er_gamma = 'Wait for market forward price'
                er_theta = 'Wait for market forward price'
                
            expected_return['ALPHA'] = er_alpha
            expected_return['GAMMA'] = er_gamma
            expected_return['THETA'] = er_theta
            
            #Uncomment this string to enable Buy/Sell
            #buy_or_sell(session, expected_return)
            
            #print statement (print, expected_return function, any of the tickers, or CAPM_vals dictionary)
            print(expected_return)
            
        
if __name__ == '__main__':
    main()  
    