# -*- coding:utf-8 -*-

from flask import Flask, render_template, redirect, url_for, request, jsonify
import pymysql
from conf import config as cf
from utils import utils as ut

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('stock_basic'))


@app.route('/stock_basic')
def stock_basic():

    query_key = 'symbol'
    query_value = request.values.get('search_words') or '000001'
    if not query_value.isdigit():
        query_key = 'name'

    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()

    # query infos from table stock
    fields = ','.join(map(lambda k: k[0], cf.TABLE_SCHEMA['stock']))
    sql = "SELECT {} FROM {} WHERE {}='{}' LIMIT 1".format(fields, 'stock', query_key, query_value)
    ret = cursor.execute(sql)
    res = cursor.fetchone()

    # put useful infos into basic
    basic = []
    ts_code = ''
    for i in range(len(cf.TABLE_SCHEMA['stock'])):
        if ret > 0:
            basic.append([cf.TABLE_SCHEMA['stock'][i][0], res[i]])
            if cf.TABLE_SCHEMA['stock'][i][0] == 'ts_code':
                ts_code = res[i]
        else:
            basic.append([cf.TABLE_SCHEMA['stock'][i][0], '暂无信息'])
            
    dates = []
    prices = []
    if ts_code != '':

        # query prices from table stock_daily
        table_stock_daily = "stock_daily_{}".format(ut.table_shardid(ts_code, 10))
        sql = "SELECT trade_date,open,close,low,high FROM {} WHERE ts_code='{}' AND trade_date<='{}' ORDER BY trade_date".format(table_stock_daily, ts_code, '20201231')
        ret = cursor.execute(sql)
        res = cursor.fetchall()
        
        # put useful infos into dates and prices
        for item in res:
            dates.append(item[0].strftime('%Y-%m-%d'))
            prices.append([str(e) for e in item[1:5]])
        
    cursor.close()
    conn.close()
    
    return render_template('stock_basic.html', search_words = query_value, basic = basic, dates = dates, prices = prices)


@app.route('/query_sug', methods = ['POST'])
def query_sug():
    query = ut.value_escape(request.form['query'])
    sql = ''
    if query.isdigit():
        sql = "SELECT symbol FROM stock WHERE symbol LIKE '{}%' LIMIT 10".format(query)
    else:
        sql = "SELECT name FROM stock WHERE name LIKE '%{}%'".format(query)
    
    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()
    ret = cursor.execute(sql)
    res = cursor.fetchall()
    cursor.close()
    conn.close()
            
    return jsonify([item[0] for item in res])


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
    
