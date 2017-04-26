import datetime

from flask import jsonify
from flask import request

from spudbin.app import app

from spudbin.storage import Database
from spudbin.storage import Humans, Human
from spudbin.storage import Templates, Template
from spudbin.storage import Records, Record
from spudbin.storage import Associations, Association

CONNECTION = Database.connection()

HUMANS = Humans(CONNECTION)
TEMPLATES = Templates(CONNECTION)
ASSOCIATIONS = Associations(CONNECTION)
RECORDS = Records(CONNECTION)

def filter_keys(dic, keys):
    filtered = dict(dic)
    for key in keys:
        if key in filtered:
            del filtered[key]
    return filtered

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
    human = HUMANS.fetch_by_login(user)
    return jsonify([filter_keys(x._asdict(), ['human'])
                    for x in ASSOCIATIONS.fetch_by_human(human)])

@app.route('/<string:user>/templates/<int:template_id>', methods=['POST'])
def assign_template_for_user(user, template_id):
    start_date = datetime.datetime.strptime(request.get_json()['startDate'], '%Y-%m-%d').date()
    human = HUMANS.fetch_by_login(user)
    template = TEMPLATES.fetch_by_pkey(template_id)

    ASSOCIATIONS.create(Association(pkey=None,
                                    human=human,
                                    template=template,
                                    start_date=start_date,
                                    end_date=None))
    return 'OKAY'

@app.route("/<string:user>/templates/<date:date>", methods=['GET'])
def get_template_by_human_date(user, date):
    human = HUMANS.fetch_by_login(user)
    association = ASSOCIATIONS.fetch_by_human_date(human, date)
    return jsonify(association.template._asdict())

# Tokens:
@app.route("/<string:user>/tokens/<date:date>", methods=['POST'])
def submit_tokens(user, date):
    """This method basically highlights everything that is shitty about my code"""
    human = HUMANS.fetch_by_login(user)
    template = ASSOCIATIONS.fetch_by_human_date(human, date).template

    # We should make this guy atomic:
    RECORDS.delete_by_human_date(human, date)

    # We should validate somet of this stuffs! Like the total count and the buckets being in
    # the template!

    buckets = request.get_json()['buckets']
    for allocation in buckets:

        record = Record(human=human,
                        date=date,
                        template=template,
                        code=allocation['bucket'],
                        tokens=allocation['tokens'])
        RECORDS.create(record)

    return jsonify(list(RECORDS.fetch_by_human_date(human, date)))

@app.route("/<string:user>/tokens/<date:date>", methods=['GET'])
def get_tokens(user, date):
    human = HUMANS.fetch_by_login(user)
    return jsonify(RECORDS.fetch_by_human_date(human, date))
