import json
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

    def __init__(self):
        self._load_schema_if_necessary()

    def row_to_entity(self, row, connection):
        return Template(pkey=row['pkey'],
                        template=json.loads(row['template']),
                        enabled=row['enabled'] == 1)

    @staticmethod
    def validate_json_template(template):
        print 'Validating template:'
        print 'Contains maxTokens:', 'maxTokens' in template
        print 'maxTokens is integer:', isinstance(template['maxTokens'], int)
        print 'maxTokens is > 0:', template['maxTokens'] > 0
        print 'Contains buckets:', 'buckets' in template
        print 'buckets is a list:', isinstance(template['buckets'], list)
        print 'buckets > 0:', len(template['buckets']) > 0
        print 'all buckets contain a bucket:', len(filter(lambda x: 'bucket' not in x, template['buckets'])) == 0
        return 'maxTokens' in template \
           and isinstance(template['maxTokens'], int) \
           and template['maxTokens'] > 0 \
           and 'buckets' in template \
           and isinstance(template['buckets'], list) \
           and len(template['buckets']) > 0 \
           and len(filter(lambda x: 'bucket' not in x, template['buckets'])) == 0

    def create(self, template, connection):
        sql = 'insert into templates(pkey, template, enabled) values (?,?,?)'
        cursor = connection.execute(sql, (template.pkey, json.dumps(template.template), 1 if template.enabled else 0,))
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id

    def update(self, template, connection):
        sql = 'update template set template = ?, enabled = ? where pkey = ?'
        connection.execute(sql, (template.pkey, template.template, 1 if template.enabled else 0,))
