from flask import jsonify
from flask import request

from spudbin.app import app

from spudbin.storage import Database
from spudbin.storage import Humans, Human
from spudbin.storage import Templates, Template
from spudbin.storage import Records, Record

CONNECTION = Database.connection()

HUMANS = Humans(CONNECTION)
TEMPLATES = Templates(CONNECTION)
RECORDS = Records(CONNECTION)

# Templates:
@app.route('/templates', methods=['GET'])
def get_templates():
    return jsonify([x._asdict() for x in TEMPLATES.all()])

@app.route("/templates", methods=['POST'])
def create_template():
    if not Templates.validate_json_template(request.get_json()):
        return 'Invalid template object', 400
    row_id = TEMPLATES.create(Template(pkey=None,
                                       template=request.get_json(),
                                       enabled=True))
    return jsonify(TEMPLATES.fetch_by_pkey(row_id)._asdict())

@app.route("/templates/<int:template_id>", methods=['GET'])
def get_template_by_id(template_id):
    return jsonify(TEMPLATES.fetch_by_pkey(template_id)._asdict())


# User templates:
@app.route('/<string:user>/templates', methods=['GET'])
def get_templates_for_user(user):
    return jsonify([x._asdict() for x in TEMPLATES.fetch_by_human(user)])

@app.route('/<string:user>/templates/<int:template_id>', methods=['POST'])
def assign_template_for_user(user, template_id):
    start_date = request.get_json['startDate']
    human = HUMANS.fetch_by_login(user)
    template = TEMPLATES.fetch_by_pkey(template_id)

    TEMPLATES.allocate_to_human(human, template, start_date)

@app.route("/<string:user>/templates/<date:date>", methods=['GET'])
def get_template_by_human_date(user, date):
    return jsonify(user=user,
                   date=date,
                   template={'id': 1,
                             'maxTokens': 8,
                             'buckets':[{'bucket': 'working',
                                         'tags': ['good'],
                                         'description': 'working hard, yeah'},
                                        {'bucket': 'slacking',
                                         'tags': ['bad'],
                                         'description': 'mooching around, wasting time'}]
                            }
                  )


# Tokens:
@app.route("/<string:user>/tokens/<date:date>", methods=['POST'])
def submit_tokens(user, date):
    human = HUMANS.fetch_by_login(user)

    RECORDS.delete_by_human_date(human, date)

    template = TEMPLATES.fetch_by_pkey(1)
    record = Record(human=human,
                    date=date,
                    template=template,
                    code='ABC123',
                    tokens=4)
    RECORDS.create(record)
    return 'OKAY'

@app.route("/<string:user>/tokens/<date:date>", methods=['GET'])
def get_tokens(user, date):
    return 'OKAY'


