import yaml
import os
from tushare.pro import data_pro as ts
import pandas as pd
import pymysql
import datetime
from utils import utils as ut
import threading
import decimal
import logging

logging.basicConfig(level = logging.INFO,
                    format = "%(asctime)s %(levelname)s %(message)s",
                    datefmt = '%Y-%m-%d %H:%M:%S'
)

class insertUpdateThread (threading.Thread):
    def __init__(self, threadID, conn, cursor, df, table, nshards):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.conn = conn
        self.cursor = cursor
        self.df = df
        self.table = table
        self.nshards = nshards
        
    def run(self):
        insert_and_update(self.conn, self.cursor, self.df, self.table, self.threadID, self.nshards)

        
def insert_and_update(conn, cursor, df, table, threadID = 0, nshards = 1):
    
    cnt_query, cnt_insert, cnt_update = 0, 0, 0
    
    for _, row in df.iterrows():
        if 'ts_code' in df.columns and ut.table_shardid(row['ts_code'], nshards) != threadID:
            continue

        # upper bounds and lower bounds
        ut.value_bounds(row)

        table_shard = table + '_' + str(threadID) if nshards > 1 else table
        clause_select = ','.join([name for name in df.columns])
        clause_where = " AND ".join(map(lambda k: "{} = '{}'".format(k, row[k]), ut.primary_key(table)))
        sql_query = "SELECT {} FROM {} WHERE {};".format(clause_select, table_shard, clause_where)
        try:
            ret_query = cursor.execute(sql_query)
            res_query = cursor.fetchall()
        except Exception as err:
            logging.error(err)
            raise(err)
        else:
            cnt_query += 1
        if ret_query == 0:
            # insert
            clause_insert_keys = clause_select
            clause_insert_values = ','.join(map(lambda k: '\"{}\"'.format(ut.value_escape(row[k])) if not pd.isnull(row[k]) else 'NULL', df.columns))
            sql_insert = "INSERT INTO {} ({}) VALUES ({})".format(table_shard, clause_insert_keys, clause_insert_values)
            logging.debug(sql_insert)
            try:
                ret = cursor.execute(sql_insert)
                conn.commit()
            except Exception as err:
                logging.info(sql_insert)
                logging.error(err)
            else:
                cnt_insert += 1
        else:
            # update
            df_query = pd.DataFrame(list(res_query), columns = df.columns)
            need_update = False
            clause_set = []
            for name in df.columns:
                if not pd.isnull(row[name]) and not ut.value_eq(row[name], df_query.loc[0][name]):
                    need_update = True
                    clause_set.append("{}=\"{}\"".format(name, ut.value_escape(row[name])))
            if need_update:
                sql_update = "UPDATE {} SET {} WHERE {};".format(table_shard, ','.join(clause_set), clause_where)
                logging.debug(sql_update)
                try:
                    ret = cursor.execute(sql_update)
                    conn.commit()
                except Exception as err:
                    logging.info(sql_update)
                    logging.error(err)
                else:
                    cnt_update += 1
                
    logging.info('Thread {}: query {} times, insert {} times, update {} times'.format(threadID, cnt_query, cnt_insert, cnt_update))
                

def collect_stock_basic(pro, fields):
    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()
    df = pro.stock_basic(fields = fields)
    insert_and_update(conn, cursor, df, 'stock')
    cursor.close()
    conn.close()

    
def collect_stock_company(pro, fields):
    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()    
    df = pro.stock_company(fields = fields)
    insert_and_update(conn, cursor, df, 'stock')    
    cursor.close()
    conn.close()    

    
def collect_exchange_open(pro, start_date, end_date, fields):
    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()        
    df = pro.trade_cal(exchange = 'SSE', start_date = start_date, end_date = end_date, fields = fields)
    insert_and_update(conn, cursor, df, 'exchange_daily')
    df = pro.trade_cal(exchange = 'SZSE', start_date = start_date, end_date = end_date, fields = fields)
    insert_and_update(conn, cursor, df, 'exchange_daily')    
    cursor.close()
    conn.close()     

    
def collect_adj_factor(pro, date, fields, nshards):
    df = pro.adj_factor(trade_date = date.strftime("%Y%m%d"), fields = fields)
    multithreads_run(df, 'stock_daily', nshards)

    
def collect_daily(pro, date, fields, nshards):
    df = pro.daily(trade_date = date.strftime("%Y%m%d"), fields = fields)
    df.rename(columns = {'change' : 'chg'}, inplace = True)
    multithreads_run(df, 'stock_daily', nshards)

    
def collect_daily_basic(pro, date, fields, nshards):
    df = pro.daily_basic(trade_date = date.strftime("%Y%m%d"), fields = fields)
    multithreads_run(df, 'stock_daily', nshards)       

    
def multithreads_run(df, table, nshards):
    conns, cursors, threads = [], [], []
    for i in range(nshards):
        conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
        cursor = conn.cursor()
        thread = insertUpdateThread(i, conn, cursor, df, table, nshards)
    
        conns.append(conn)
        cursors.append(cursor)
        threads.append(thread)
    
        threads[i].start()    
    
    for i in range(nshards):
        threads[i].join()
    
    for i in range(nshards):
        cursors[i].close()
        conns[i].close()       
        
    
def daily_wrapper(pro, start_date, end_date, func, fields, nshards):
    start = datetime.date(start_date // 10000, start_date % 10000 // 100, start_date % 100)
    end = datetime.date(end_date // 10000, end_date % 10000 // 100, end_date % 100)
    delta = datetime.timedelta(days = 1)
    date = start
    while date <= end:
        logging.info('FUNC: ' + func.__name__ + ' DATE: ' + date.strftime("%Y-%m-%d"))
        func(pro, date, fields, nshards)
        date += delta
 

if __name__ == "__main__":

    conf_file = os.path.join(os.path.abspath('.'), 'conf', 'spider_batch.yaml')
    with open(conf_file, 'r', encoding = 'utf-8') as fs:
        conf_dict = yaml.load(fs, Loader = yaml.FullLoader)

    pro = ts.pro_api()
    nthreads_stock_daily = 10
        
    if 'stock_basic' in conf_dict and conf_dict['stock_basic']['enable']:
        conf = conf_dict['stock_basic']
        collect_stock_basic(pro, conf['fields'])

    if 'stock_company' in conf_dict and conf_dict['stock_company']['enable']:
        conf = conf_dict['stock_company']
        collect_stock_company(pro, conf['fields'])

    if 'exchange_open' in conf_dict and conf_dict['exchange_open']['enable']:
        conf = conf_dict['exchange_open']
        collect_exchange_open(pro, conf['start_date'], conf['end_date'], conf['fields'])
        
    if 'daily' in conf_dict and conf_dict['daily']['enable']:
        conf = conf_dict['daily']
        daily_wrapper(pro, conf['start_date'], conf['end_date'], collect_daily, conf['fields'], nthreads_stock_daily)
        
    if 'adj_factor' in conf_dict and conf_dict['adj_factor']['enable']:
        conf = conf_dict['adj_factor']
        daily_wrapper(pro, conf['start_date'], conf['end_date'], collect_adj_factor, conf['fields'], nthreads_stock_daily)

    if 'daily_basic' in conf_dict and conf_dict['daily_basic']['enable']:
        conf = conf_dict['daily_basic']
        daily_wrapper(pro, conf['start_date'], conf['end_date'], collect_daily_basic, conf['fields'], nthreads_stock_daily)
