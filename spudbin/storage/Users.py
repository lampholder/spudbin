"""Storage classes for Users"""
from collections import namedtuple
from spudbin.storage import Store

User = namedtuple('User', ['pkey', 'username'])

class Users(Store):
    """Storage class for Users"""

    table_name = 'users'
    schema = \
        """
        drop table if exists users;
        create table users (
            pkey integer primary key,
            username text not null,
            constraint username_unique unique(username)
        );
        """

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()

    def row_to_entity(self, row):
        return User(pkey=row['pkey'],
                    username=row['username'])

    def fetch_by_username(self, username):
        """Fetch the user from the db by the username"""
        cursor = self._connection.cursor()
        sql = 'select * from users where username = ?'
        cursor.execute(sql, (username, ))
        return self.one_or_none(cursor)

    def delete_by_username(self, username):
        """Delete the user from storage referenced by the username"""
        cursor = self._connection.cursor()
        sql = 'delete from users where username = ?'
        cursor.execute(sql, (username,))
        self._connection.commit()
        cursor.close()

    def create(self, user):
        """Create and persist a new user"""
        cursor = self._connection.cursor()
        sql = 'insert into users (pkey, username) values (?,?)'
        cursor.execute(sql, (user.pkey, user.username, ))
        self._connection.commit()
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id

    def update(self, user):
        """Update an existing user"""
        cursor = self._connection.cursor()
        sql = 'update users set username = ? where pkey = ?'
        cursor.execute(sql, (user.pkey, user.username, ))
        self._connection.commit()
        cursor.close()
