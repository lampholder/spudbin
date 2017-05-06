import json
from collections import namedtuple
from spudbin.storage import Store

Template = namedtuple('Template', ['pkey', 'buckets', 'maxTokens', 'layout', 'enabled'])

class Templates(Store):

    table_name = 'templates'
    schema = \
        """
        drop table if exists %s;
        create table %s (
            pkey integer primary key,
            maxTokens integer not null,
            buckets text not null,
            layout text,
            enabled integer not null
        );
        """ % (table_name, table_name)

    def __init__(self):
        self._load_schema_if_necessary()

    def row_to_entity(self, row, connection):
        template_json_blob = json.loads(row['template'])
        return Template(pkey=row['pkey'],
                        buckets=template_json_blob.get('buckets'),
                        maxTokens=template_json_blob.get('maxTokens'),
                        layout=template_json_blob.get('layout', None),
                        enabled=row['enabled'] == 1)

    @staticmethod
    def validate_json_template(template):
        valid_format = 'maxTokens' in template \
           and isinstance(template['maxTokens'], int) \
           and template['maxTokens'] > 0 \
           and 'buckets' in template \
           and isinstance(template['buckets'], list) \
           and len(template['buckets']) > 0 \
           and len(filter(lambda x: 'bucket' not in x,
                          template['buckets'])) == 0

        if 'layout' in template:
            buckets = [bucket['bucket'] for bucket in template['buckets']]
            for row in template['layout']:
                for item in row:
                    if item['type'] == 'bucket' and item['value'] not in buckets:
                        print 'Layout references unknown bucket:', item['value']
                        return False
        return valid_format

    def create(self, template, connection):
        sql = 'insert into templates(pkey, maxTokens, buckets, layout, enabled) values (?,?,?)'
        cursor = connection.execute(sql, (template.pkey,
                                          template.maxTokens,
                                          json.dumps(template.buckets),
                                          json.dumps(template.layout),
                                          1 if template.enabled else 0,))
        insert_id = cursor.lastrowid
        cursor.close()
        return insert_id

    def update(self, template, connection):
        sql = 'update template set maxtTokens = ?, buckets = ?, layout = ?, enabled = ? where pkey = ?'
        connection.execute(sql, (template.pkey,
                                 template.maxTokens,
                                 json.dumps(template.buckets),
                                 json.dumps(template.layout),
                                 1 if template.enabled else 0,))
