"""Classes for persisting token counts for a given day"""
import datetime
from collections import namedtuple

from spudbin.storage import Store
from spudbin.storage import Users
from spudbin.storage import Templates

Record = namedtuple('Record', ['user', 'date', 'template', 'code', 'tokens'])

class Records(Store):
    """Record tokens for a given day."""

    table_name = 'records'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            user_pkey integer not null,
            date text not null,
            template_pkey integer not null,
            code text not null,
            tokens integer not null,
            constraint user_date_code_unique unique(user_pkey, date, code)
        );
        """ % (table_name, table_name)

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()
        self._users = Users(connection)
        self._templates = Templates(connection)

    def row_to_entity(self, row):
        return Record(user=self._users.fetch_by_pkey(row['user_pkey']),
                      date=datetime.datetime.strptime(row['date'], '%Y-%m-%d').date(),
                      template=self._templates.fetch_by_pkey(row['template_pkey']),
                      code=row['code'],
                      tokens=row['tokens'])

    def fetch_by_user_date(self, user, date):
        """Fetch records for a given user on a given date."""
        cursor = self._connection.cursor()
        sql = 'select * from records where user_pkey = ? and date = ?'
        cursor.execute(sql, (user.pkey, datetime.datetime.strftime(date, '%Y-%m-%d', )))
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            yield self.row_to_entity(row)

    def delete_by_user_date(self, user, date):
        """Delete token records for a given user on a given date."""
        cursor = self._connection.cursor()
        sql = 'delete from %s where user_pkey = ? and date = ?' % self.table_name
        cursor.execute(sql, (user.pkey, datetime.datetime.strftime(date, '%Y-%m-%d'),))
        self._connection.commit()
        cursor.close()

    def create(self, record):
        """Drop some tokens in a bucket!"""
        #TODO: Replace this with a thing that only allows valid tokenising to be done
        cursor = self._connection.cursor()
        sql = 'insert into records(user_pkey, date, template_pkey, code, tokens) ' + \
              'values (?,?,?,?,?)'
        cursor.execute(sql, (record.user.pkey,
                             datetime.datetime.strftime(record.date, '%Y-%m-%d'),
                             record.template.pkey,
                             record.code, record.tokens, ))
        self._connection.commit()
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id
