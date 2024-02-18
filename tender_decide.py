# -*- coding: utf-8 -*-
import pandas as pd


# 算order book的weighted成本，和tender比较

def VWAP(r,num):
  df=pd.DataFrame()
  df['price']=r['price']
  df['vol']=r['quantity']-r['quantity_filled']
  df['cum']=df['vol'].cumsum()
  df.index=range(0,len(df))
  temp=df[df['cum']>=num]
  if len(temp)==0:
    out=len(df)
    print(temp)
    print(out)
  else:
    out=temp.index[0]
  v=(df['price']*df['vol'])[0:out].sum()+df['price'].iloc[out]*(num-df['cum'].iloc[out-1])
  # print('df:',df)
  print('vwap:',v)
  print('num:',num)
  return v/num
    

def tender(ritc,pos,limit):
  info=ritc.get_tenders()
  #print(len(info))
  if len(info)==0:
    retmsg='No tender!'
    return -1,0,retmsg
  else:
    if list(info['action'])==['BUY']:
      label=1
    else:
      label=-1
    cost=float(info['price'])
    num=int(info['quantity'])
    time=int(info['tick'])
    idt=str(info['tender_id'][0])
    if label==1:
      r=ritc.bid('RITC',20)
    else:
      r=ritc.ask('RITC',20)  
    v=VWAP(r,num)
    if abs(pos)>=50000 and pos*label<0: # 方向相反 我的pos非常大
      retmsg='Due to the opposite position.'
      return 1,idt,retmsg
    if time>=limit: # 没时间清仓了 dan'zui'ho
      retmsg='Due to the time limit.'
      return 0,idt,retmsg
    if cost*label>v*label: # 成本过大
      retmsg='Due to the cost is high(vwap: %f, cost: %f)!' %(v,cost) 
      return 0,idt,retmsg
    elif abs(cost-v)>0.02: #change here! 越大要求越高！
      retmsg='Due to the high premium %f!' %(abs(cost-v))
      return 1,idt,retmsg
    else:
      retmsg='Due to the premium is %f, not good!' %(abs(cost-v))
      return 0,idt,retmsg
      
    
    
    
    
    
    
  
  