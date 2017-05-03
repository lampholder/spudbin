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

    def __init__(self):
        self._load_schema_if_necessary()

    def row_to_entity(self, row, connection):
        return User(pkey=row['pkey'],
                    username=row['username'])

    def fetch_by_username(self, username, connection):
        """Fetch the user from the db by the username"""
        sql = 'select * from users where username = ?'
        cursor = connection.execute(sql, (username, ))
        return self.one_or_none(cursor)

    def delete_by_username(self, username, connection):
        """Delete the user from storage referenced by the username"""
        sql = 'delete from users where username = ?'
        connection.execute(sql, (username,))

    def create(self, user, connection):
        """Create and persist a new user"""
        sql = 'insert into users (pkey, username) values (?,?)'
        cursor = connection.execute(sql, (user.pkey, user.username, ))
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id

    def update(self, user, connection):
        """Update an existing user"""
        sql = 'update users set username = ? where pkey = ?'
        connection.execute(sql, (user.pkey, user.username, ))
