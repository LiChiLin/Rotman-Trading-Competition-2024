import signal
import requests
from time import sleep
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import cvxpy as cp

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

API_KEY = {"X-API-Key": "K5X4BO4C"}
shutdown = False
session = requests.Session()
session.headers.update(API_KEY)

# code that gets the current tick
def get_tick(session):
    resp = session.get("http://localhost:9999/v1/case")
    if resp.ok:
        case = resp.json()
        return case["tick"]
    raise ApiException("fail - cant get tick")

# code that parses the first and latest news instances for forward market predictions and the risk free rate
# Important: this code only works if the only '%' character is in front of the RISK FREE RATE and the onle '$' character is in front of the forward price suggestions
def get_news(session):
    news = session.get("http://localhost:9999/v1/news")
    if news.ok:
        newsbook = news.json()
        for i in range(len(newsbook[-1]["body"])):
            if newsbook[-1]["body"][i] == "%":
                CAPM_vals["%Rf"] = round(
                    float(newsbook[-1]["body"][i - 4 : i]) / 100, 4
                )
        latest_news = newsbook[0]
        if len(newsbook) > 1:
            for j in range(len(latest_news["body"]) - 1, 1, -1):
                while latest_news["body"][j] != "$":
                    j -= 1
            CAPM_vals["forward"] = float(latest_news["body"][j + 1 : -1])
        return CAPM_vals
    raise ApiException("timeout")

# gets all the price data for all securities
def pop_prices(session):
    price_act = session.get("http://localhost:9999/v1/securities")
    if price_act.ok:
        prices = price_act.json()
        return prices
    raise ApiException("fail - cant get securities")


# Mean-Variance Portfolio Optimization function
def mean_variance_optimization_cvxpy(expected_returns, cov_matrix):
    num_assets = len(expected_returns)
    
    # Define the weights variable
    weights = cp.Variable(num_assets)
    
    # Portfolio variance, which is a quadratic form
    portfolio_variance = cp.quad_form(weights, cov_matrix)
    
    # Expected portfolio return
    portfolio_return = weights @ expected_returns
    
    # Objective function: minimize the portfolio variance
    objective = cp.Minimize(portfolio_variance)
    
    # Constraints: sum of weights = 1, weights are between 0 and 1 (long only portfolio)
    constraints = [cp.sum(weights) == 1, weights >= -1, weights <= 1]
    
    # Define and solve the problem
    problem = cp.Problem(objective, constraints)
    problem.solve()

    # The optimal weights
    return weights.value


# Buy or Sell function
def buy_or_sell(weights, current_positions, gross_limit, net_limit):
    base_position_size = 10000
    if weights[0] >= 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "ALPHA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[0],
                    "action": "BUY",
                },
            )
    
    if weights[0] < 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "ALPHA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[0],
                    "action": "SELL",
                },
            )
    
    if weights[1] >= 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "GAMMA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[1],
                    "action": "BUY",
                },
            )
    
    if weights[1] < 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "GAMMA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[1],
                    "action": "SELL",
                },
            )
    
    if weights[2] >= 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "THETA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[2],
                    "action": "BUY",
                },
            )
    
    if weights[2] < 0:
        session.post(
                "http://localhost:9999/v1/orders",
                params={
                    "ticker": "THETA",
                    "type": "MARKET",
                    "quantity": base_position_size * weights[2],
                    "action": "SELL",
                },
            )

def main():
    with requests.Session() as session:
        session.headers.update(API_KEY)
        ritm = pd.DataFrame(columns=["RITM", "BID", "ASK", "LAST", "%Rm"])
        alpha = pd.DataFrame(
            columns=["ALPHA", "BID", "ASK", "LAST", "%Ri", "%Rm", "position"]
        )
        gamma = pd.DataFrame(
            columns=["GAMMA", "BID", "ASK", "LAST", "%Ri", "%Rm", "position"]
        )
        theta = pd.DataFrame(columns=["THETA", "BID", "ASK", "LAST", "%Ri", "%Rm"])


        # Initialize a variable to track the warm-up period
        warmup_period = 30  # seconds
        start_tick = None  # This will hold the starting tick
        current_positions = {"ALPHA": 0, "GAMMA": 0, "THETA": 0}

        # Trading limits
        gross_limit = 250000
        net_limit = 100000

        alpha_historical_data = []
        gamma_historical_data = []
        theta_historical_data = []

        while get_tick(session) < 600 and not shutdown:
            # update the forward market price and rf rate
            get_news(session)
            current_tick = get_tick(session)


            # Set the start tick at the beginning of the trading session
            if start_tick is None:
                start_tick = current_tick


            ##update RITM bid-ask dataframe
            pdt_RITM = pd.DataFrame(pop_prices(session)[0])
            ritmp = pd.DataFrame(
                {
                    "RITM": "",
                    "BID": pdt_RITM["bid"],
                    "ASK": pdt_RITM["ask"],
                    "LAST": pdt_RITM["last"],
                    "%Rm": "",
                }
            )
            if ritm["BID"].empty or ritmp["LAST"].iloc[0] != ritm["LAST"].iloc[0]:
                ritm = pd.concat([ritmp, ritm.loc[:]]).reset_index(drop=True)
                ritm["%Rm"] = (ritm["LAST"] / ritm["LAST"].shift(-1)) - 1
                if ritm.shape[0] >= 31:
                    ritm = ritm.iloc[:30]


            # generate expected market return paramter
            if "forward" in CAPM_vals.keys():
                CAPM_vals["%RM"] = (CAPM_vals["forward"] - ritm["LAST"].iloc[0]) / ritm[
                    "LAST"
                ].iloc[0]
            else:
                CAPM_vals["%RM"] = ""


            ##update ALPHA bid-ask dataframe
            pdt_ALPHA = pd.DataFrame(pop_prices(session)[1])
            alphap = pd.DataFrame(
                {
                    "ALPHA": "",
                    "BID": pdt_ALPHA["bid"],
                    "ASK": pdt_ALPHA["ask"],
                    "LAST": pdt_ALPHA["last"],
                    "%Ri": "",
                    "%Rm": "",
                    "position": pdt_ALPHA["position"],
                }
            )
            if alpha["BID"].empty or alphap["LAST"].iloc[0] != alpha["LAST"].iloc[0]:
                alpha = pd.concat([alphap, alpha.loc[:]]).reset_index(drop=True)
                alpha["%Ri"] = (alpha["LAST"] / alpha["LAST"].shift(-1)) - 1
                alpha["%Rm"] = (ritm["LAST"] / ritm["LAST"].shift(-1)) - 1
                if alpha.shape[0] >= 31:
                    alpha = alpha.iloc[:30]


            ##update GAMMA bid-ask dataframe
            pdt_GAMMA = pd.DataFrame(pop_prices(session)[2])
            gammap = pd.DataFrame(
                {
                    "GAMMA": "",
                    "BID": pdt_GAMMA["bid"],
                    "ASK": pdt_GAMMA["ask"],
                    "LAST": pdt_GAMMA["last"],
                    "%Ri": "",
                    "%Rm": "",
                    "position": pdt_GAMMA["position"],
                }
            )
            if gamma["BID"].empty or gammap["LAST"].iloc[0] != gamma["LAST"].iloc[0]:
                gamma = pd.concat([gammap, gamma.loc[:]]).reset_index(drop=True)
                gamma["%Ri"] = (gamma["LAST"] / gamma["LAST"].shift(-1)) - 1
                gamma["%Rm"] = (ritm["LAST"] / ritm["LAST"].shift(-1)) - 1
                if gamma.shape[0] >= 31:
                    gamma = gamma.iloc[:30]


            ##update THETA bid-ask dataframe
            pdt_THETA = pd.DataFrame(pop_prices(session)[3])
            thetap = pd.DataFrame(
                {
                    "THETA": "",
                    "BID": pdt_THETA["bid"],
                    "ASK": pdt_THETA["ask"],
                    "LAST": pdt_THETA["last"],
                    "%Ri": "",
                    "%Rm": "",
                }
            )
            if theta["BID"].empty or thetap["LAST"].iloc[0] != theta["LAST"].iloc[0]:
                theta = pd.concat([thetap, theta.loc[:]]).reset_index(drop=True)
                theta["%Ri"] = (theta["LAST"] / theta["LAST"].shift(-1)) - 1
                theta["%Rm"] = (ritm["LAST"] / ritm["LAST"].shift(-1)) - 1
                if theta.shape[0] >= 31:
                    theta = theta.iloc[:30]


            beta_alpha = (alpha["%Ri"].cov(ritm["%Rm"])) / (ritm["%Rm"].var())
            beta_gamma = (gamma["%Ri"].cov(ritm["%Rm"])) / (ritm["%Rm"].var())
            beta_theta = (theta["%Ri"].cov(ritm["%Rm"])) / (ritm["%Rm"].var())


            CAPM_vals["Beta - ALPHA"] = beta_alpha
            CAPM_vals["Beta - GAMMA"] = beta_gamma
            CAPM_vals["Beta - THETA"] = beta_theta


            if CAPM_vals["%RM"] != "":
                er_alpha = CAPM_vals["%Rf"] + CAPM_vals["Beta - ALPHA"] * (
                    CAPM_vals["%RM"] - CAPM_vals["%Rf"]
                )
                er_gamma = CAPM_vals["%Rf"] + CAPM_vals["Beta - GAMMA"] * (
                    CAPM_vals["%RM"] - CAPM_vals["%Rf"]
                )
                er_theta = CAPM_vals["%Rf"] + CAPM_vals["Beta - THETA"] * (
                    CAPM_vals["%RM"] - CAPM_vals["%Rf"]
                )
            else:
                er_alpha = "Wait for market forward price"
                er_gamma = "Wait for market forward price"
                er_theta = "Wait for market forward price"


            expected_return["ALPHA"] = er_alpha
            expected_return["GAMMA"] = er_gamma
            expected_return["THETA"] = er_theta

            if not np.isnan(alpha["LAST"]) and not np.isnan(gamma["LAST"]) and not np.isnan(theta["LAST"]):
                alpha_historical_data.append(alpha["LAST"])
                gamma_historical_data.append(gamma["LAST"])
                theta_historical_data.append(theta["LAST"])

                if len(alpha_historical_data) > 30:
                    alpha_historical_data.pop(0)
                    gamma_historical_data.pop(0)
                    theta_historical_data.pop(0)
                
                # Convert lists to numpy arrays
                alpha_prices = np.array(alpha_historical_data)
                gamma_prices = np.array(gamma_historical_data)
                theta_prices = np.array(theta_historical_data)

                # Calculate log returns
                alpha_returns = np.diff(np.log(alpha_prices))
                gamma_returns = np.diff(np.log(gamma_prices))
                theta_returns = np.diff(np.log(theta_prices))

                # Stack the returns into a matrix where each column represents an asset's returns
                returns_matrix = np.column_stack((alpha_returns, gamma_returns, theta_returns))

                # Calculate the covariance matrix of returns
                cov_matrix = np.cov(returns_matrix, rowvar=False)
            
            if start_tick % 5 ==0 and warmup_period > 30:
                # Now call the buy_or_sell function
                weights = mean_variance_optimization_cvxpy (list(expected_return.values()), cov_matrix)
                buy_or_sell(session, weights, current_positions, gross_limit, net_limit)


if __name__ == "__main__":
    main()



