import json
import datetime
from collections import namedtuple
from spudbin.storage import Store

Template = namedtuple('Template', ['pkey', 'template', 'enabled'])

class Templates(Store):

    table_name = 'templates'
    schema = \
        """
        drop table if exists templates;
        create table templates (
            pkey integer primary key,
            template text not null,
            enabled integer not null
        );
        drop table if exists human_templates;
        create table human_templates (
            human_pkey integer not null,
            template_pkey integer not null,
            start_date text not null,
            end_date text not null
        );
        """

    def __init__(self, connection):
        self._connection = connection
        self._load_schema_if_necessary()

    def row_to_entity(self, row):
        return Template(pkey=row['pkey'],
                        template=json.loads(row['template']),
                        enabled=row['enabled'] == 1)

    @staticmethod
    def validate_json_template(template):
        return 'maxTokens' in template \
           and isinstance(template['maxTokens'], int) \
           and template['maxTokens'] > 0 \
           and 'buckets' in template \
           and isinstance(template['buckets'], list) \
           and len(template['buckets']) > 0 \
           and len(filter(lambda x: 'bucket' not in x, template['buckets'])) == 0

    def create(self, template):
        cursor = self._connection.cursor()
        sql = 'insert into templates(pkey, template, enabled) values (?,?,?)'
        cursor.execute(sql, (template.pkey, json.dumps(template.template), 1 if template.enabled else 0,))
        self._connection.commit()
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id

    def update(self, template):
        cursor = self._connection.cursor()
        sql = 'update template set template = ?, enabled = ? where pkey = ?'
        cursor.execute(sql, (template.pkey, template.template, 1 if template.enabled else 0,))
        self._connection.commit()
        cursor.close()

    def allocate_to_human(self, human, template, start_date):
        templates = list(self.fetch_by_human(human))
        if len(templates) == 0:
            cursor = self._connection.cursor()
            sql = 'insert into human_templates(human_pkey, template_pkey, start_date, end_date) ' + \
                  'values (?,?,?,?)'
            cursor.execute(sql, (human.pkey, template.pkey, '0-01-01', '9000-01-01'))
            self._connection.commit()
        else:
            template_to_modify = [x for x in templates
                                  if x.start_date < start_date and x.end_date > start_date][0]
            template_to_modify.end_date = start_date
            self.update(template_to_modify)
            cursor = self._connection.cursor()
            sql = 'insert into human_templates(human_pkey, template_pkey, start_date, end_date) ' + \
                  'values (?,?,?,?)'
            cursor.execute(sql, (human.pkey, template.pkey,
                                 datetime.datetime.strftime(start_date, '%Y-%m-%d'),
                                 '9000-01-01'))
            self._connection.commit()

    def fetch_by_human(self, human):
        cursor = self._connection.cursor()
        sql = 'select template_pkey, start_date, end_date from human_templates' + \
              ' where human_pkey = ?'
        cursor.execute(sql, (human.pkey, ))
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            yield {'start': datetime.datetime.strptime(row['start_date'], '%Y-%m-%d'),
                   'end': datetime.datetime.strptime(row['start_date'], '%Y-%m-%d'),
                   'template': self.fetch_by_pkey(row['template_pkey'])}

