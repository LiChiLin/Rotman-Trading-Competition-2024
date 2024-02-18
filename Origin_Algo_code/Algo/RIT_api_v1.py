import requests
import pandas as pd

class RitClient():

    def __init__(self, url, apikey):

        self.url = url
        self.apikey = apikey


    def get_request(self, command, params={}, table=False):
        resp = requests.get(self.url + command, headers=self.apikey, params=params)
        #print(resp)
        if resp.status_code == 200:
            resp = resp.json()
            if table:
                if type(resp) == dict:
                    return pd.DataFrame([resp])
                return pd.DataFrame(resp)
            return resp
        else:
            resp = resp.json()
            print("Operation Failed")
            print(resp["message"])
            return resp
    
    def post_request(self, command, params={}, table=False):
        resp = requests.post(self.url + command, headers=self.apikey, params=params)
        if resp.status_code == 200:
            resp = resp.json()
            if table:
                if type(resp) == dict:
                    return pd.DataFrame([resp])
                return pd.DataFrame(resp)
            return resp
        else:
            resp = resp.json()
            print("Operation Failed")
            print(resp["message"])
            return resp
    
    def delete_request(self, command, params={}, table=False):
        resp = requests.delete(self.url + command, headers=self.apikey, params=params)
        if resp.status_code == 200:
            resp = resp.json()
            if table:
                if type(resp) == dict:
                    return pd.DataFrame([resp])
                return pd.DataFrame(resp)
            return resp
        else:
            resp = resp.json()
            print("Operation Failed")
            print(resp["message"])
            return resp

    def case(self, table=True):
        return self.get_request("case", table=table)

    def trader(self, table=True):
        return self.get_request("trader", table=table).set_index("trader_id")

    def limits(self, table=True):
        return self.get_request("limits", table=table).set_index("name")

    def news(self):
        return self.get_request("news", table=True).set_index("news_id")

    def assets(self, ticker=None):
        return self.get_request("assets", params={"ticker": ticker}, table=True)#.set_index("news_id")

    def securities(self, ticker=None):
        return self.get_request("securities", params={"ticker": ticker}, table=True).set_index("ticker")

    def securities_book(self, ticker, limit=20):
        book = self.get_request("securities/book", params={"ticker": ticker, "limit": limit}, table=False)
        book["bids"] = pd.DataFrame(book["bids"]).set_index("ticker")
        book["asks"] = pd.DataFrame(book["asks"]).set_index("ticker")
        return book
        
    def securities_history(self, ticker, period=None, limit=None):
        return self.get_request("securities/history", params={"ticker": ticker, "period": period, "limit": limit}, table=True).set_index("tick")

    def get_orders_all(self, status=None):
        return self.get_request("orders", params={"status": status}, table=True)

    def get_orders_id(self, identity):
        return self.get_request("orders/" + str(identity), table=True)

    def post_orders(self, ticker, otype, quantity, action, price=None, dry_run=0):
        return self.post_request("orders", params={"ticker": ticker, "type": otype, "quantity": quantity, "action": action, "price": price, "dry_run": dry_run}, 
                            table=True)

    def delete_orders(self, identity):
        return self.delete_request("orders/" + str(identity), table=True)

    def cancel(self, isall=0, ticker=None, ids=[], query=""):
        return self.post_request("commands/cancel", params={"all": isall, "ticker": ticker, "ids": ids, "query": query}, table=True)

    def get_tenders(self):
        return self.get_request("tenders", table=True)

    def post_tenders(self, identity, price=None):
        return self.post_request("tenders/" + str(identity), params={"price": price}, table=True)

    def delete_tenders(self, identity):
        return self.delete_request("tenders/" + str(identity), table=True)

    def case_tick(self):
        return self.case()[["tick", "ticks_per_period", "period", "total_periods"]].values

    # Check Active or Not
    def case_status(self):
        if self.case()["status"].values == "ACTIVE":
            return True
        return False

    # Trader Name
    def trader_infoself(self):
        return self.trader()

    # Order Limit
    def limit_info(self):
        return self.limits()

    # Get News
    def news_info(self, reverse=True):
        return self.news().sort_index(ascending=not reverse)

    # Get Full Market
    def market(self):
        return self.securities()

    # Get Full Market Price
    def market_price(self):
        return self.securities()["last"]

    # Get Limit Book
    def book(self, ticker, line=20):
        return self.securities_book(ticker, line)

    # Get Ask
    def ask(self, ticker, line=20):
        return self.book(ticker, line)["asks"]

    # Get Bid
    def bid(self, ticker, line=20):
        return self.book(ticker, line)["bids"]

    # Get Historic Price
    def history(self, ticker, reverse=True, period=None, limit=None):
        return self.securities_history(ticker, period, limit).sort_index(ascending=not reverse)

    # Market Operation Below

    # Get Posted Orders
    def order(self, identity=None):
        if identity:
            return self.get_orders_id(identity)
        return self.get_orders_all()

    # Market Order Simulation Price
    def market_sim_buy(self, ticker, quantity):
        return self.post_orders(ticker, "MARKET", quantity, "BUY", None, dry_run=1)
        
    def market_sim_sell(self, ticker, quantity):
        return self.post_orders(ticker, "MARKET", quantity, "SELL", None, dry_run=1)

    # Market BUY
    def market_buy(self, ticker, quantity):
        return self.post_orders(ticker, "MARKET", quantity, "BUY", None, dry_run=0)

    # Market SELL
    def market_sell(self, ticker, quantity):
        return self.post_orders(ticker, "MARKET", quantity, "SELL", None, dry_run=0)

    # Limit BUY
    def limit_buy(self, ticker, quantity, price):
        return self.post_orders(ticker, "LIMIT", quantity, "BUY", price, dry_run=0)

    # Limit SELL
    def limit_sell(self, ticker, quantity, price):
        return self.post_orders(ticker, "LIMIT", quantity, "SELL", price, dry_run=0)

    # Delete Posted Order
    def delete(self, identity):
        return self.delete_orders(identity)

    # Unsucessful Request
    # Do NOT Use
    '''
    def delete_all():
        return cancel(1)

    '''

    # Batch Delete By Order Ticker
    def delete_byticker(self, ticker):
        return self.cancel(ticker=ticker)

    # Batch Delete By Order ID
    def delete_byid(self, identity):
        return self.cancel(ids=identity)

    # Batch Delete By Query
    # SQL-Like, Columns Including "Volume", "Ticker" and "Price"
    def delete_byquery(self, query):
        return self.cancel(query=query)

    # Tender
    # Refer to Last Block

