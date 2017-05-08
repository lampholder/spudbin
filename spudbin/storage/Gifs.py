"""Classes for persisting token counts for a given day"""
import datetime
from collections import namedtuple
from spudbin.storage import Store

Gif = namedtuple('Gif', ['date', 'url'])

class Gifs(Store):
    """Record gifs for a given day."""

    table_name = 'gifs'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            date text not null,
            url text not null,
            constraint date_unique unique(date)
        );
        """ % (table_name, table_name)

    def __init__(self):
        self._load_schema_if_necessary()

    def row_to_entity(self, row, connection):
        return Gif(date=datetime.datetime.strptime(row['date'], '%Y-%m-%d'),
                   url=row['url'])

    def fetch_by_date(self, date, connection):
        """Fetch the gif for a given date."""
        sql = 'select * from gifs where date = ?'
        cursor = connection.execute(sql, (datetime.datetime.strftime(date, '%Y-%m-%d', )))
        return self.one_or_none(cursor)

    def delete_by_date(self, date, connection):
        """Delete gif for a given date."""
        sql = 'delete from %s where date = ?' % self.table_name
        connection.execute(sql, (datetime.datetime.strftime(date, '%Y-%m-%d'),))

    def create(self, gif, connection):
        """Store a gif"""
        sql = 'insert into gifs(date, url) ' + \
              'values (?,?)'
        cursor = connection.execute(sql, (gif.date,
                                          gif.url, ))
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id
