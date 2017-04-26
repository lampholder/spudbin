from collections import namedtuple
from spudbin.storage import Store

Human = namedtuple('Human', ['pkey', 'login', 'access_token'])

class Humans(Store):

    table_name = 'humans'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            pkey integer primary key,
            login text not null,
            access_token text not null,
            constraint login_unique unique(login)
        );
        """ % (table_name, table_name)

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()

    def row_to_entity(self, row):
        return Human(pkey=row['pkey'],
                     login=row['login'],
                     access_token=row['access_token'])

    def fetch_by_login(self, login):
        cursor = self._connection.cursor()
        sql = 'select * from humans where login = ?'
        cursor.execute(sql, (login, ))
        return self.one_or_none(cursor)

    def delete_by_login(self, login):
        cursor = self._connection.cursor()
        sql = 'delete from %s where login = ?' % self.table_name
        cursor.execute(sql, (login,))
        self._connection.commit()
        cursor.close()

    def create(self, human):
        cursor = self._connection.cursor()
        sql = 'insert into humans(pkey, login, access_token) values (?,?,?)'
        cursor.execute(sql, (human.pkey, human.login, human.access_token,))
        self._connection.commit()
        cursor.close()

    def update(self, human):
        cursor = self._connection.cursor()
        sql = 'update humans set login = ?, access_token = ? where pkey = ?'
        cursor.execute(sql, (human.pkey, human.login, human.access_token,))
        self._connection.commit()
        cursor.close()
