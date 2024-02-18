# -*- coding: utf-8 -*-
"""
ROTMAN TRADING COMPITATION
Quantitative Outcry

Created on Sun Feb 16 11:31:10 2020

@author: Jincheng Dan
"""

'''this is a half automatic program, formated data can be processed automatically,
   half formated data need key board input, for totally unformated data we use 
   specific changes at the end.
'''



import API_new
import numpy as np
import pandas as pd
import time

countries = ['Canada', 'USA', 'China', 'Brazil', 'Germany', 'South Africa']
quarters = ['first', 'second', 'third', 'fourth']
Q_GDP_previous = pd.DataFrame(np.zeros([4,6]), columns = countries )
Q_GDP_now = pd.DataFrame(np.zeros([4,6]), columns = countries )
Q_GDP_estimate = pd.DataFrame(np.zeros([4,6]), columns = countries )
RT_index = 1000
old_tick = 0

s = [pd.DataFrame(np.zeros([1,3]), columns =['Manufactured', 'Service', 'Raw Material']) for i in range(Q_GDP_previous.shape[1])]
Sector = pd.DataFrame([s], columns = countries)

keyheader = {'X-API-Key':'6D4BPW7Q'}
url = 'http://localhost:9999/v1/'

#Canada-ca, USA-us, China-ch, Brazil-br, Germany-ge, South Africa-sa
short = ['ca', 'us', 'ch', 'br', 'ge', 'sa']
def input_country(head, body):
    print()
    print(head)
    print(body)
    st=input('input country name:')
    country=''
    if st =='q':
        return 'input end'
    try:
        country = countries[short.index(st)]
    except:
        input_country()      
    return country

def input_sectors(body, country):
    '''input format as 'dd dd dd', dd is the number before the persentage sign
    '''
    print()
    print(body)
    change=input('input spercentage change: manufacture, service, row material:\n')
#    sector=pd.DataFrame(np.zeros([1,3]),columns = ['Manufactured', 'Service', 'Raw Material'] )
    if change =='q':
        return 'input end'
    try:
        changes = change.split(' ')
        print(changes)
        Sector[country][0]['Manufactured'] *= (1+float(changes[0])/100)
        Sector[country][0]['Service'] *= (1+float(changes[1])/100)
        Sector[country][0]['Raw Material'] *= (1+float(changes[2])/100)
    except:
        input_sectors(country) 

def input_data(head, body, RT_index):
    if 'ESTIMATES' in head and 'GDP' in head:
            
        country = body.split('\'s')[0]
    #    quarter = int(head.split(' ')[1][1])
        
    #    quarter = int(head[head.find('GDP')-2])
        quarter = quarters.index(body.split('quarter')[0].split(' ')[-2])+1
        gdp = float(body.split(',')[0].split(' ')[-2][1:])
        Q_GDP_previous.iat[quarter-1, countries.index(country)] = gdp
        
        Sector[country][0]['Manufactured'] = float(body.split(',')[2].split(' ')[-4][1:])
        Sector[country][0]['Service'] = float(body.split(',')[3].split(' ')[1][1:])
        Sector[country][0]['Raw Material'] = float(body.split(',')[3].split(' ')[-5][1:])
        
        Q_GDP_estimate.iat[quarter-1, countries.index(country)] = \
              Sector[country][0]['Manufactured']+Sector[country][0]['Service']+Sector[country][0]['Row Material']
              
        estimate_RT = RT_index + np.sum(np.sum(Q_GDP_estimate-Q_GDP_previous))
        print('estimate_RT : %f    %s has been added' % (estimate_RT, country))
        
    elif '|' in body and 'Index' in body:
        body = (' '+body+' ').split('|')
        for i in range(6):
            quarter = int(body[i].split(' ')[-4][1])
            country = body[i].split('Q')[0][1:][:-1]
            value = float(body[i].split(' ')[-2][:-1][1:])
            Q_GDP_now.iat[quarter-1,countries.index(country)] = value
        
           
        estimate_RT = RT_index + np.sum(np.sum(Q_GDP_estimate-Q_GDP_previous))
        
        RT_index = float(body[-1].split(' ')[-2])
        print('realized_RT : %f' % RT_index)
        print('estimate_RT : %f' % estimate_RT)
        
    elif 'RIT' in body:
        estimate_RT = RT_index + np.sum(np.sum(Q_GDP_estimate-Q_GDP_previous))
        c = float(input('global change in RIT:'))
        print('estimate_RT : %f' % (estimate_RT*(1+c)))
        
    else:
        '''Canada-ca, USA-us, China-ch, Brazil-br, Germany-ge, South Africa-sa'''
        quarter = 5-np.sum(Q_GDP_now['Canada']==0)
        country = input_country(head, body)
        input_sectors(body, country)
        Q_GDP_estimate.iat[quarter-1, countries.index(country)] = \
              Sector[country][0]['Manufactured']+Sector[country][0]['Service']+Sector[country][0]['Raw Material']
        
        estimate_RT = RT_index + np.sum(np.sum(Q_GDP_estimate-Q_GDP_previous))
        print('estimate_RT : %f     %s has been added' % (estimate_RT, country))
    time.sleep(1)
    return RT_index




def add_data(k=0, old_tick = old_tick):
    '''add one missing news, k the the tick the the news need to be added
    '''
    outcry = RitClient(url, keyheader)
    '''The value of the RT100 Index is determined by the quarterly changes in GDP, 
       in $ billions, of the following 6 economies: Canada, the United States, 
       China, Brazil, Germany, and South Africa.
    '''
    #news = outcry.news()
    n = outcry.news()
    tick = n['tick'][n['tick'].index[0]]
    if k != 0:
        head = n['headline'][n['tick']==k][n['body'][n['tick']==k].index[0]]
        body = n['body'][n['tick']==k][n['body'][n['tick']==k].index[0]]
        tick = k
        old_tick = k
        global RT_index
        RT_index = input_data(head, body, RT_index)
        
 
            
def keep_running():
    '''keep processing news
    '''
    global old_tick
    while 1: 
        outcry = RitClient(url, keyheader)
        '''The value of the RT100 Index is determined by the quarterly changes in GDP, 
           in $ billions, of the following 6 economies: Canada, the United States, 
           China, Brazil, Germany, and South Africa.
        '''
        #news = outcry.news()
        n = outcry.news()
        tick = n['tick'][n['tick'].index[0]]           
        if tick != old_tick:
            old_tick = tick
    
            head = n['headline'][n.index[0]]
            body = n['body'][n.index[0]]
            global RT_index
            RT_index = input_data(head, body, RT_index)
            

keep_running()
#these are for specific multiple changes at one time
            
            
#countries = ['Canada', 'USA', 'China', 'Brazil', 'Germany', 'South Africa']
#['Manufactured', 'Service', 'Raw Material']
#
#Sector['Canada'][0]['Manufactured'] *= 1
#Sector['Canada'][0]['Service'] *= 1
#Sector['Canada'][0]['Raw Material'] *= 1
#
#print("estimated RIT %f" % np.sum(np.sum(Sector))

    
    
    
