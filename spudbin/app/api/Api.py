import json

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

@app.route("/template/<string:user>/<date:date>", methods=['GET'])
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

# Templates:
@app.route("/template", methods=['POST'])
def create_template():
    row_id = TEMPLATES.create(Template(pkey=None,
                                       template=json.dumps(request.get_json()),
                                       enabled=True))
    return jsonify(TEMPLATES.fetch_by_pkey(row_id))

@app.route("/template/<int:id>", methods=['GET'])
def get_template_by_id(template_id):
    return jsonify(TEMPLATES.fetch_by_pkey(template_id))


# Tokens:
@app.route("/tokens/<string:user>/<date:date>", methods=['POST'])
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

@app.route("/tokens/<string:user>/<date:date>", methods=['GET'])
def get_tokens(user, date):
    return 'OKAY'


