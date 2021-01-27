
create table exchange_daily (
       exchange varchar(5) not null,
       cal_date date not null,
       is_open tinyint(1) default 0,
       primary key (exchange, cal_date)
       ) engine = InnoDB default charset = utf8;

