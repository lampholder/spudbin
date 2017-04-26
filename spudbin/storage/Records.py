import datetime
from collections import namedtuple

from spudbin.storage import Store
from spudbin.storage import Humans
from spudbin.storage import Templates

Record = namedtuple('Record', ['human', 'date', 'template', 'code', 'tokens'])

class Records(Store):

    table_name = 'records'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            human_pkey integer not null,
            date text not null,
            template_pkey integer not null,
            code text not null,
            tokens integer not null,
            constraint date_code_unique unique(date, code)
        );
        """ % (table_name, table_name)

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()
        self._humans = Humans(connection)
        self._templates = Templates(connection)

    def row_to_entity(self, row):
        return Record(human=self._humans.fetch_by_pkey(row['human_pkey']),
                      date=datetime.datetime.strptime(row['date'], '%Y-%m-%d'),
                      template=self._templates.fetch_by_pkey(row['template_pkey']),
                      code=row['code'],
                      tokens=row['tokens'])

    def fetch_by_human_date(self, human, date):
        cursor = self._connection.cursor()
        sql = 'select * from records where human = ? and date = ?'
        cursor.execute(sql, (human.pkey, datetime.datetime.strftime(date, '%Y-%m-%d', )))
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            yield self.row_to_entity(row)

    def delete_by_human_date(self, human, date):
        cursor = self._connection.cursor()
        sql = 'delete from %s where human = ? and date = ?' % self.table_name
        cursor.execute(sql, (human.pkey, datetime.datetime.strftime(date, '%Y-%m-%d'),))
        self._connection.commit()
        cursor.close()

    def create(self, record):
        self.delete_by_human_date(record.human, record.date)
        cursor = self._connection.cursor()
        sql = 'insert into records(human_pkey, date, template_pkey, code, tokens) ' + \
              'values (?,?,?,?,?)'
        cursor.execute(sql, (record.human.pkey, record.date, record.template.pkey,
                             record.code, record.tokens, ))
        self._connection.commit()
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id
