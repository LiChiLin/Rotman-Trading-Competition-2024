# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 02:06:22 2019

@author: Yufeng Zhang

Contact: zyf2516@bu.edu

"""

import time
import numpy as np
import pandas as pd
from RIT_api_v1 import *
#import statsmodels.tsa.stattools as ts
#from BACKUP2_GFTD import *
from tender_decide import *

#from Model_probit import *
# initializing
url = 'http://localhost:9999/v1/'
keyheader = {'X-API-Key': '6D4BPW7Q'}
ritc = RitClient(url, keyheader)
# variables
tickers = ['BULL', 'BEAR', 'RITC']
accept_buy = {'BULL': 1, 'BEAR': 1, 'RITC': 1}
accept_sell = {'BULL': 1, 'BEAR': 1, 'RITC': 1}
order_list = {
    'BULL': {
        'BUY': [], 'SELL': []}, 'BEAR': {
            'BUY': [], 'SELL': []}, 'RITC': {
                'BUY': [], 'SELL': []}}
# timingnum=5000
limit_a = 0.04
mmjump = 0.01
mmnum = 1500
time_lim = 250
delete = 10

# Connect and Wait for start
while ritc.case_status() == False:
    time.sleep(0.2)

while(ritc.case_status() == True):

    time.sleep(1)

    for x in tickers:
        # beg=time.time()

        pos = int(ritc.securities(x)['position'])
        diff = float(ritc.securities(x)['unrealized']) / max(pos, 1)
        ask = float(ritc.ask(x, 1)['price'])
        bid = float(ritc.bid(x, 1)['price'])
        time1 = ritc.case_tick()[0][0]
        #print('Time: %d' %time1)

        if diff < 0 and (abs(pos) >= 5000 or abs(diff) > 0.35):
            count_buy = count_sell = 0
            if pos < 0:
                l = len(order_list[x]['SELL'])
                tick = min(l, delete)
                ritc.delete_byid(order_list[x]['SELL'][0:tick])
                print('Deleted order:', order_list[x]['SELL'][0:tick])
                order_list[x]['SELL'] = order_list[x]['SELL'][tick:]
                if accept_sell[x] > 0:
                    accept_sell[x] -= 0.5
                order_list[x]['BUY'] += [int(ritc.limit_buy(x,
                                                            mmnum, bid + mmjump * 5)['order_id'])]
            elif pos > 0:
                l = len(order_list[x]['BUY'])
                tick = max(l, delete)
                ritc.delete_byid(order_list[x]['BUY'][0:tick])
                print('Deleted order:', order_list[x]['BUY'][0:tick])
                order_list[x]['BUY'] = order_list[x]['BUY'][tick:]
                if accept_buy[x] > 0:
                    accept_buy[x] -= 0.5
                order_list[x]['SELL'] += [
                    int(ritc.limit_sell(x, mmnum, ask - mmjump * 5)['order_id'])]
        else:
            if accept_buy[x] < 1:
                count_buy += 1
                if count_buy % 5 == 0:
                    accept_buy[x] += 0.5
            if accept_sell[x] < 1:
                count_sell += 1
                if count_sell % 5 == 0:
                    accept_sell[x] += 0.5
        if abs(ask - bid) > limit_a:
            if accept_buy[x] > 0:
                order_list[x]['BUY'] += [int(ritc.limit_buy(x,
                                                            mmnum *
                                                            accept_buy[x],
                                                            bid + mmjump)['order_id'])]
                print('Make buy order:', x, 'by ', mmnum * accept_buy[x])
            if accept_sell[x] > 0:
                order_list[x]['SELL'] += [
                    int(ritc.limit_sell(x, mmnum * accept_sell[x], ask - mmjump)['order_id'])]
                print('Make sell order:', x, 'by ', mmnum * accept_buy[x])

        if x == 'RITC':
            x, idt, msg = tender(ritc, pos, time_lim)
            if x != -1:
                print('\n*****************************')
                if x == 0:
                    ritc.delete_tenders(idt)
                    print('Tender %s declined! %s' % (idt, msg))
                elif x == 1:
                    ritc.post_tenders(idt)
                    print('Tender %s accpeted! %s' % (idt, msg))
                print('*****************************')

        # end=time.time()
        # print('time',end-beg)


        time.sleep(0.3)
