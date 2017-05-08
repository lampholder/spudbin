"""Abstract storage impl."""
from spudbin.storage import Database

class Store(object):
    """Abstract db storage class, implementing some common stuff."""

    table_name = None
    schema = None

    def _table_exists(self):
        with Database.connection() as connection:
            sql = 'select name from sqlite_master where type=\'table\' and name=?'
            cursor = connection.execute(sql, (self.table_name, ))
            table = cursor.fetchall()
            cursor.close()
            return len(table) == 1

    def _load_schema_if_necessary(self):
        if not self._table_exists():
            with Database.connection() as connection:
                connection.executescript(self.schema)

    def row_to_entity(self, row, connection):
        """Should take a row from the db and hydrate to a useful entity object."""
        pass

    def all(self, connection):
        """Fetch all of the entities in this table; return as a generator."""
        sql = 'select * from %s' % self.table_name
        cursor = connection.execute(sql)
        rows = cursor.fetchall()
        return [self.row_to_entity(row, connection) for row in rows]

    def fetch_by_pkey(self, pkey, connection):
        """Fetch the entity by its pkey"""
        sql = 'select * from %s where pkey = ?' % self.table_name
        cursor = connection.execute(sql, (pkey, ))
        return self.one_or_none(cursor)

    def delete_by_pkey(self, pkey, connection):
        """Delete the entity referenced by its pkey"""
        sql = 'delete from %s where pkey = ?' % self.table_name
        connection.execute(sql, (pkey,))

    def one_or_none(self, cursor):
        """Safely fetches at most one record from the db. If more match the query it
        suggests we have a nasty problem :)"""
        first_row = cursor.fetchone()
        second_row = cursor.fetchone()

        if second_row is None and first_row is not None:
            cursor.close()
            return self.row_to_entity(first_row, cursor.connection)
        elif first_row is None:
            cursor.close()
            return None
        else:
            cursor.close()
            raise Exception('Multiple rows found for what should have been a unique query.')
