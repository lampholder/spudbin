import json
import datetime
from collections import namedtuple
from spudbin.storage import Store

Template = namedtuple('Template', ['pkey', 'template', 'enabled'])

class Templates(Store):

    table_name = 'templates'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            pkey integer primary key,
            template text not null,
            enabled integer not null
        );
        """ % (table_name, table_name)

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
