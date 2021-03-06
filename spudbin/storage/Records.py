"""Classes for persisting token counts for a given day"""
import datetime
from collections import namedtuple

from spudbin.storage import Store
from spudbin.storage import Users
from spudbin.storage import Templates

Record = namedtuple('Record', ['user', 'date', 'template', 'bucket', 'tokens'])

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
            bucket text not null,
            tokens integer not null,
            constraint user_date_bucket_unique unique(user_pkey, date, bucket)
        );
        """ % (table_name, table_name)

    def __init__(self):
        self._load_schema_if_necessary()
        self._users = Users()
        self._templates = Templates()

    def row_to_entity(self, row, connection):
        return Record(user=self._users.fetch_by_pkey(row['user_pkey'], connection),
                      date=datetime.datetime.strptime(row['date'], '%Y-%m-%d').date(),
                      template=self._templates.fetch_by_pkey(row['template_pkey'], connection),
                      bucket=row['bucket'],
                      tokens=row['tokens'])

    def fetch_by_user_date(self, user, date, connection):
        """Fetch records for a given user on a given date."""
        sql = 'select * from records where user_pkey = ? and date = ?'
        cursor = connection.execute(sql, (user.pkey, datetime.datetime.strftime(date, '%Y-%m-%d', )))
        rows = cursor.fetchall()
        cursor.close()
        return [self.row_to_entity(row, connection) for row in rows]

    def delete_by_user_date(self, user, date, connection):
        """Delete token records for a given user on a given date."""
        sql = 'delete from %s where user_pkey = ? and date = ?' % self.table_name
        connection.execute(sql, (user.pkey, datetime.datetime.strftime(date, '%Y-%m-%d'),))

    def create(self, record, connection):
        """Drop some potatoes in a bin!"""
        sql = 'insert into records(user_pkey, date, template_pkey, bucket, tokens) ' + \
              'values (?,?,?,?,?)'
        cursor = connection.execute(sql, (record.user.pkey,
                                          datetime.datetime.strftime(record.date, '%Y-%m-%d'),
                                          record.template.pkey,
                                          record.bucket, record.tokens, ))
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id
