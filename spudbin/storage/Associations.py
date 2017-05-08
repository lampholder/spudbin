import json
import datetime
from collections import namedtuple
from spudbin.storage import Store
from spudbin.storage import Users
from spudbin.storage import Templates

Association = namedtuple('Association', ['pkey', 'user', 'template', 'start_date', 'end_date'])

class Associations(Store):

    table_name = 'user_templates'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            pkey integer primary key,
            user_pkey integer not null,
            template_pkey integer not null,
            start_date text not null,
            end_date text not null
        );
        """ % (table_name, table_name)

    def __init__(self):
        self._load_schema_if_necessary()
        self._users = Users()
        self._templates = Templates()

    def row_to_entity(self, row, connection):
        return Association(pkey=row['pkey'],
                           user=self._users.fetch_by_pkey(row['user_pkey'], connection),
                           template=self._templates.fetch_by_pkey(row['template_pkey'], connection),
                           start_date=datetime.datetime.strptime(row['start_date'],
                                                                 '%Y-%m-%d').date(),
                           end_date=datetime.datetime.strptime(row['end_date'], '%Y-%m-%d').date())

    def update(self, association, connection):
        """Update a user/template association by its pkey."""
        sql = 'update user_templates set start_date = ?, end_date = ? where pkey = ?'
        cursor = connection.execute(sql, (datetime.datetime.strftime(association.start_date, '%Y-%m-%d'),
                                    datetime.datetime.strftime(association.end_date, '%Y-%m-%d'),
                                    association.pkey, ))

    def create(self, association, connection):
        """Create an association between a user and a template. For any user with associations,
        for any given day they must have an association.
        What this means is, for the first association, the window details are ignored - that
        association is set for and from all time. Any subequent windows will interrupt
        existing windows."""
        associations = list(self.fetch_by_user(association.user, connection))
        if len(associations) == 0:
            # If there are no existing associations, this association is put in place
            # for all time :)
            sql = 'insert into user_templates(user_pkey, template_pkey, start_date, ' + \
                  'end_date) values (?,?,?,?)'
            cursor = connection.execute(sql, (association.user.pkey,
                                        association.template.pkey,
                                        '1900-01-01',
                                        '9000-01-01'))
        else:
            """Cases we need to handle:

              All time: |AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA|
            New assoc.: |AAAAAAAAAAAAAAAAAAAAAAAAAAAA|BBBBBB|AAAAAAAAAAAAAAAAAAAAA|
            New assoc.: |AAAAAAAAAAA|CCCCCC|AAAAAAAAA|BBBBBB|AAAAAAAAAAAAAAAAAAAAA|
            New assoc.: |AAAAAAAAAAA|CCC|DDDDDDD|AAAA|BBBBBB|AAAAAAAAAAAAAAAAAAAAA|
            New assoc.: |AAAAAAAAAAA|CCC|DDD|EEEEEEEEEEEE|BB|AAAAAAAAAAAAAAAAAAAAA|

            So, enumerating instructions:
             - any existing associations entirely within the new window should be removed
             - any existing associations who end after the start of the new window
               should be truncated
             - any existing associations who start before the end of the new window
               should be delayed
            """
            # Delete any associations that are within the new window.
            sql = 'delete from user_templates where user_pkey = ? and start_date >= ? and end_date <= ?'
            connection.execute(sql, (association.user.pkey,
                                     association.start_date,
                                     association.end_date, ))

            # Truncate an association that starts before the new window and ends within the new window
            truncate_sql = 'update user_templates set end_date = ? where user_pkey = ? and ' + \
                           'start_date < ? and end_date > ?'
            connection.execute(truncate_sql, (association.start_date - datetime.timedelta(days=1),
                                              association.user.pkey,
                                              association.start_date,
                                              association.start_date, ))

            # Delay an associatione that starts within the new window and ends outside the new window
            delay_sql = 'update user_templates set start_date = ? where user_pkey = ? and ' + \
                        'start_date < ? and end_date > ?'
            connection.execute(delay_sql, (association.end_date + datetime.timedelta(days=1),
                                           association.user.pkey,
                                           association.end_date,
                                           association.end_date, ))

            # Insert the new association window
            new_sql = 'insert into user_templates(user_pkey, template_pkey, start_Date, ' + \
                      'end_date) values (?,?,?,?)'
            connection.execute(new_sql, (association.user.pkey,
                                         association.template.pkey,
                                         association.start_date,
                                         association.end_date, ))



    def fetch_by_user(self, user, connection):
        """Fetch the template associations for a given user."""
        sql = 'select pkey, user_pkey, template_pkey, start_date, end_date ' + \
              'from user_templates where user_pkey = ?'
        cursor = connection.execute(sql, (user.pkey, ))
        rows = cursor.fetchall()
        cursor.close()
        return [self.row_to_entity(row, connection) for row in rows]

    def fetch_by_user_date(self, user, date, connection):
        """Fetch the template association for a given user on a given date."""
        sql = 'select pkey, user_pkey, template_pkey, start_date, end_date ' + \
              'from user_templates where user_pkey = ? and start_date <= ? ' + \
              'and end_date > ?'
        cursor = connection.execute(sql, (user.pkey, date, date, ))
        return self.one_or_none(cursor)
