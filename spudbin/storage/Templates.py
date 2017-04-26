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
                        template=row['template'],
                        enabled=row['enabled'] == 1)

    def create(self, template):
        cursor = self._connection.cursor()
        sql = 'insert into templates(pkey, template, enabled) values (?,?,?)'
        cursor.execute(sql, (template.pkey, template.template, template.enabled,))
        self._connection.commit()
        cursor.close()

    def update(self, template):
        cursor = self._connection.cursor()
        sql = 'update template set template = ?, enabled = ? where pkey = ?'
        cursor.execute(sql, (template.pkey, template.template, template.enabled,))
        self._connection.commit()
        cursor.close()

