# -*- coding:utf-8 -*-

import datetime
import decimal


def table_shardid(ts_code, nshards):
    return int(ts_code[0:6]) % nshards


def value_escape(value):
    if isinstance(value, str):
        value = value.replace('%', '%%').replace("\\", "\\\\").replace("\'", "\\\'").replace("\"", "\\\"")
    return value


def value_eq(ts_value, db_value):
    if isinstance(db_value, datetime.date):
        db_value = db_value.strftime("%Y%m%d")
    elif isinstance(db_value, decimal.Decimal):
        db_value = float(db_value)
    return ts_value == db_value


def primary_key(table):
    if table == 'stock':
        return ['ts_code']
    elif table == 'exchange_daily':
        return ['exchange', 'cal_date']
    elif table == 'stock_daily':
        return ['ts_code', 'trade_date']
    else:
        return []

def value_bounds(row):
    for key in ['ps_ttm', 'pe_ttm']:
        if key in row and row[key] > 999999.9999:
            row[key] = 999999.9999

    for key in ['dv_ratio', 'dv_ttm']:
        if key in row and row[key] > 99.9999:
            row[key] = 99.9999
            
if __name__ == '__main__':
    print('test')

    
