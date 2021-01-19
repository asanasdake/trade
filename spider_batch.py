# -*- coding:utf-8 -*-

import yaml
import os
from tushare.pro import data_pro as ts
import pandas as pd
from pandas.io import sql
from sqlalchemy import create_engine
import datetime


def value_eq(ts_value, db_value):
    if isinstance(db_value, datetime.date):
        db_value = db_value.strftime("%Y%m%d")
    return ts_value == db_value


def sql_value_escape(value):
    if isinstance(value, str):
        value = value.replace('%', '%%').replace("\\", "\\\\").replace("\'", "\\\'").replace("\"", "\\\"")
    return value


def primary_key(table):
    if table == 'stock':
        return ['ts_code']
    elif table == 'exchange_daily':
        return ['exchange', 'cal_date']
    elif table == 'stock_daily':
        return ['ts_code', 'trade_date']


def insert_and_update(df, table):
    df_insert = pd.DataFrame(columns = df.columns)
    for _, row in df.iterrows():
        clause_where = " AND ".join(map(lambda k: "{} = '{}'".format(k, row[k]), primary_key(table)))
        sql_query = "SELECT * FROM {} WHERE {};".format(table, clause_where)
        df_read = pd.read_sql_query(sql_query, engine)
        if df_read.empty:
            df_insert = df_insert.append(row, ignore_index = True, sort = False)
        else:
            need_update = False
            set_arr = []
            for index in df.columns:
                if not pd.isnull(row[index]) and not value_eq(row[index], df_read.loc[0][index]):
                    need_update = True
                    set_arr.append("{}=\"{}\"".format(index, sql_value_escape(row[index])))
            if need_update:
                sql_update = "UPDATE {} SET {} WHERE {};".format(table, ','.join(set_arr), clause_where)
                #print(sql_update)
                sql.execute(sql_update, engine)
                
    if not df_insert.empty:
        df_insert.to_sql(table, engine, index = False, if_exists = 'append')
                                                                                                                                                                                                                                

def collect_stock_basic(engine, pro, fields):
    df = pro.stock_basic(fields = fields)
    insert_and_update(df, 'stock')


def collect_stock_company(engine, pro, fields):
    df = pro.stock_company(fields = fields)
    insert_and_update(df, 'stock')

    
def collect_exchange_open(engine, pro, start_date, end_date, fields):
    df = pro.trade_cal(exchange = 'SSE', start_date = start_date, end_date = end_date, fields = fields)
    insert_and_update(df, 'exchange_daily')
    df = pro.trade_cal(exchange = 'SZSE', start_date = start_date, end_date = end_date, fields = fields)
    insert_and_update(df, 'exchange_daily')

    
def collect_daily(engine, pro, date, fields):
    df = pro.daily(trade_date = date.strftime("%Y%m%d"), fields = fields)
    df.rename(columns = {'change' : 'chg'}, inplace = True)
    insert_and_update(df, 'stock_daily')

        
def collect_adj_factor(engine, pro, date, fields):
    df = pro.adj_factor(trade_date = date.strftime("%Y%m%d"), fields = fields)
    insert_and_update(df, 'stock_daily')


def collect_daily_basic(engine, pro, date, fields):
    df = pro.daily_basic(trade_date = date.strftime("%Y%m%d"), fields = fields)
    insert_and_update(df, 'stock_daily')


def daily_wrapper(engine, pro, start_date, end_date, func, fields):
    start = datetime.date(start_date // 10000, start_date % 10000 // 100, start_date % 100)
    end = datetime.date(end_date // 10000, end_date % 10000 // 100, end_date % 100)
    delta = datetime.timedelta(days = 1)
    date = start
    while date <= end:
        print(func.__name__ + ' ' + date.strftime("%Y-%m-%d"))
        func(engine, pro, date, fields)
        date += delta
        

if __name__ == "__main__":

    engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format('root', '', 'localhost', '3306', 'trade'))
    
    conf_file = os.path.join(os.path.abspath('..'), 'conf', 'batch.yaml')
    with open(conf_file, 'r', encoding = 'utf-8') as fs:
        conf_dict = yaml.load(fs, Loader = yaml.FullLoader)

    pro = ts.pro_api()
        
    if 'stock_basic' in conf_dict and conf_dict['stock_basic']['enable']:
        collect_stock_basic(engine, pro, conf_dict['stock_basic']['fields'])

    if 'stock_company' in conf_dict and conf_dict['stock_company']['enable']:
        collect_stock_company(engine, pro, conf_dict['stock_company']['fields'])

    if 'exchange_open' in conf_dict and conf_dict['exchange_open']['enable']:
        collect_exchange_open(engine, pro, conf_dict['exchange_open']['start_date'], conf_dict['exchange_open']['end_date'], conf_dict['exchange_open']['fields'])
        
    if 'daily' in conf_dict and conf_dict['daily']['enable']:
        daily_wrapper(engine, pro, conf_dict['daily']['start_date'], conf_dict['daily']['end_date'], collect_daily, conf_dict['daily']['fields'])
        
    if 'adj_factor' in conf_dict and conf_dict['adj_factor']['enable']:
        daily_wrapper(engine, pro, conf_dict['adj_factor']['start_date'], conf_dict['adj_factor']['end_date'], collect_adj_factor, conf_dict['adj_factor']['fields'])

    if 'daily_basic' in conf_dict and conf_dict['daily_basic']['enable']:
        daily_wrapper(engine, pro, conf_dict['daily_basic']['start_date'], conf_dict['daily_basic']['end_date'], collect_daily_basic, conf_dict['daily_basic']['fields'])

        
