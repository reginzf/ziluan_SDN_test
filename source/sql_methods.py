import logging
import pymysql


class SQL:
    def __init__(self, host, user, password, port=None):
        self.host = host
        self.user = user
        self.password = password
        self.port = port

    def connect_db(self, db_name):
        try:
            res = pymysql.connect(host=self.host, user=self.user, password=self.password, database=db_name,
                                  port=self.port, cursorclass=pymysql.cursors.DictCursor)
            return res
        except Exception:
            logging.info(msg='连接db:{} 失败'.format(db_name))
            raise Exception

    def gen_cmd(self, tablename, cows='*', **kwargs):
        if type(cows) == list:
            c = ','.join(cows)
        else:
            c = cows
        if kwargs:
            condition = []
            for key, value in kwargs.items():
                condition.append("{key}='{value}'".format(key=key, value=value))
            condition = " AND ".join(condition)

            logging.info(
                msg='==>select {c} from {table} where {condition}'.format(c=c, table=tablename, condition=condition))
            return 'select {c} from {table} where {condition}'.format(c=c, table=tablename, condition=condition)
        return 'select {c} from {table} '.format(c=c, table=tablename)

    def query(self, db, table, cows='*', **kwargs):
        '''
        :param db:
        :param table:
        :param cows:
        :param kwargs: condition: where condition
        :return:
        '''
        conn = self.connect_db(db, )
        cursor = conn.cursor()
        cmd = self.gen_cmd(table, cows, **kwargs)
        try:
            cursor.execute(cmd)
        except Exception as e:
            logging.info(msg='{db} ')
        res = cursor.fetchall()
        conn.close()
        return res


if __name__ == '__main__':
    sql = SQL(host='172.25.50.25', user='moove', password='unic-moove', port=3306)
    res = sql.query('resource_core', 'azone', ['azone_id'],region_id='cd-unicloud-region')
    print(res)
