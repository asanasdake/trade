from flask import Flask, render_template, redirect, url_for, request
import pymysql
from conf import config as cf

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('stock_basic'))


@app.route('/stock_basic')
def stock_basic():

    symbol = request.values.get('symbol') or '000001'

    conn = pymysql.connect(host = "localhost", user = "root", password = "", database = "trade")
    cursor = conn.cursor()

    # query infos from table stock
    fields = ','.join(map(lambda k: k[0], cf.TABLE_SCHEMA['stock']))
    sql = "SELECT {} FROM stock WHERE symbol='{}' LIMIT 1".format(fields, symbol)
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
        sql = "SELECT trade_date,open,close,low,high FROM stock_daily WHERE ts_code='{}' AND trade_date>='{}' AND trade_date<='{}' ORDER BY trade_date".format(ts_code, '20200101', '20201231')
        ret = cursor.execute(sql)
        res = cursor.fetchall()
        
        # put useful infos into dates and prices
        for item in res:
            dates.append(item[0].strftime('%Y-%m-%d'))
            prices.append([str(e) for e in item[1:5]])
        
    cursor.close()
    conn.close()
    
    return render_template('stock_basic.html', symbol = symbol, basic = basic, dates = dates, prices = prices)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
    
