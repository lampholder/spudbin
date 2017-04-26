class Store(object):

    _connection = None
    table_name = None
    schema = None

    def _table_exists(self):
        cursor = self._connection.cursor()
        sql = 'select name from sqlite_master where type=\'table\' and name=?'
        cursor .execute(sql, (self.table_name, ))
        table = cursor.fetchall()
        cursor.close()
        return len(table) == 1

    def _load_schema_if_necessary(self):
        if not self._table_exists():
            cursor = self._connection.cursor()
            cursor.executescript(self.schema)
            self._connection.commit()
            cursor.close()

    def row_to_entity(self, row):
        pass

    def all(self):
        cursor = self._connection.cursor()
        sql = 'select * from %s' % self.table_name
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            yield self.row_to_entity(row)

    def fetch_by_pkey(self, pkey):
        cursor = self._connection.cursor()
        sql = 'select * from %s where pkey = ?' % self.table_name
        cursor.execute(sql, (pkey, ))
        return self.one_or_none(cursor)

    def delete_by_pkey(self, pkey):
        cursor = self._connection.cursor()
        sql = 'delete from %s where pkey = ?' % self.table_name
        cursor.execute(sql, (pkey,))
        self._connection.commit()
        cursor.close()

    def one_or_none(self, cursor):
        if cursor.rowcount == 0:
            cursor.close()
            return None
        elif cursor.rowcount > 1:
            cursor.close()
            raise Exception('Multiple rows found for what should have been a unique query.')
        else:
            row = cursor.fetchone()
            cursor.close()
            return self.row_to_entity(row)
