# -*- coding:utf-8 -*-

TABLE_SCHEMA = {
    'stock' : [
        ['ts_code', 'TS代码', 'key'],
        ['symbol', '股票代码', 'stock_basic'],
        ['name', '股票名称', 'stock_basic'],
        ['area', '所在地域', 'stock_basic'],
        ['industry', '所属行业', 'stock_basic'],
        ['fullname', '股票全称', 'stock_basic'],
        ['enname', '英文名称', 'stock_basic'],
        ['market', '市场类型', 'stock_basic'],
        ['exchange', '交易所代码', 'stock_basic'],
        ['curr_type', '交易货币', 'stock_basic'],
        ['list_status', '上市状态', 'stock_basic'],
        ['list_date', '上市日期', 'stock_basic'],
        ['delist_date', '退市日期', 'stock_basic'],
        ['is_hs', '是否沪深港通', 'stock_basic'],
        ['chairman', '法人代表', 'stock_company'],
        ['manager', '总经理', 'stock_company'],
        ['secretary', '董秘', 'stock_company'],
        ['reg_capital', '注册资本', 'stock_company'],
        ['setup_date', '注册日期', 'stock_company'],
        ['province', '所在省份', 'stock_company'],
        ['city', '所在城市', 'stock_company'],
        ['introduction', '公司介绍', 'stock_company'],
        ['website', '公司主页', 'stock_company'],
        ['email', '电子邮箱', 'stock_company'],
        ['office', '办公室', 'stock_company'],
        ['employees', '员工人数', 'stock_company'],
        ['main_business', '主要业务及产品', 'stock_company'],
        ['business_scope', '经营范围', 'stock_company']
        ]
}


