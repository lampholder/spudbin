import json
import datetime
from collections import namedtuple
from spudbin.storage import Store
from spudbin.storage import Humans
from spudbin.storage import Templates

Association = namedtuple('Association', ['pkey', 'human', 'template', 'start_date', 'end_date'])

class Associations(Store):

    table_name = 'human_templates'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            pkey integer primary key,
            human_pkey integer not null,
            template_pkey integer not null,
            start_date text not null,
            end_date text not null
        );
        """ % (table_name, table_name)

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()
        self._humans = Humans(connection)
        self._templates = Templates(connection)

    def row_to_entity(self, row):
        return Association(pkey=row['pkey'],
                           human=self._humans.fetch_by_pkey(row['human_pkey']),
                           template=self._templates.fetch_by_pkey(row['template_pkey']),
                           start_date=datetime.datetime.strptime(row['start_date'], '%Y-%m-%d'),
                           end_date=datetime.datetime.strptime(row['end_date'], '%Y-%m-%d'))

    def update(self, association):
        cursor = self._connection.cursor()
        sql = 'update human_templates set start_date = ?, end_date = ? where pkey = ?'
        cursor.execute(sql, (association.pkey, association.start_date, association.end_date, ))
        self._connection.commit()
        cursor.close()

    def create(self, association):
        associations = list(self.fetch_by_human(association.human))
        if len(associations) == 0:
            cursor = self._connection.cursor()
            sql = 'insert into human_templates(human_pkey, template_pkey, start_date, ' + \
                  'end_date) values (?,?,?,?)'
            cursor.execute(sql, (association.human.pkey,
                                 association.template.pkey,
                                 '0001-01-01',
                                 '9000-01-01'))
            self._connection.commit()
        else:
            association_to_modify = [x for x in associations
                                     if x.start_date < association.start_date
                                     and x.end_date > association.start_date][0]
            association_to_modify.end_date = association.start_date
            self.update(association_to_modify)

            cursor = self._connection.cursor()
            sql = 'insert into human_templates(human_pkey, template_pkey, start_date, ' + \
                  'end_date) values (?,?,?,?)'
            cursor.execute(sql, (association.human.pkey, association.template.pkey,
                                 datetime.datetime.strftime(association.start_date, '%Y-%m-%d'),
                                 '9000-01-01')) # TODO: this should be the start date of the next thing.
            self._connection.commit()

    def fetch_by_human(self, human):
        cursor = self._connection.cursor()
        sql = 'select pkey, human_pkey, template_pkey, start_date, end_date ' + \
              'from human_templates where human_pkey = ?'
        cursor.execute(sql, (human.pkey, ))
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            yield self.row_to_entity(row)

