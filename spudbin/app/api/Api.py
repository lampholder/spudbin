import datetime

from flask import jsonify
from flask import request

from spudbin.app import app

from spudbin.storage import Database
from spudbin.storage import Users, User
from spudbin.storage import Templates, Template
from spudbin.storage import Records, Record
from spudbin.storage import Associations, Association

CONNECTION = Database.connection()

USERS = Users(CONNECTION)
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
@app.route('/<string:username>/templates', methods=['GET'])
def get_templates_for_user(username):
    user = USERS.fetch_by_username(username)
    return jsonify([filter_keys(x._asdict(), ['user'])
                    for x in ASSOCIATIONS.fetch_by_user(user)])

@app.route('/<string:username>/templates/<int:template_id>', methods=['POST'])
def assign_template_for_user(username, template_id):
    start_date = datetime.datetime.strptime(request.get_json()['startDate'], '%Y-%m-%d').date()
    user = USERS.fetch_by_username(username)
    template = TEMPLATES.fetch_by_pkey(template_id)

    ASSOCIATIONS.create(Association(pkey=None,
                                    user=user,
                                    template=template,
                                    start_date=start_date,
                                    end_date=None))
    return 'OKAY'

@app.route("/<string:username>/templates/<date:date>", methods=['GET'])
def get_template_by_user_date(username, date):
    user = USERS.fetch_by_username(username)
    association = ASSOCIATIONS.fetch_by_user_date(user, date)
    return jsonify(association.template._asdict())

# Tokens:
@app.route("/<string:username>/tokens/<date:date>", methods=['POST'])
def submit_tokens(username, date):
    """This method basically highlights everything that is shitty about my code"""
    user = USERS.fetch_by_username(username)
    template = ASSOCIATIONS.fetch_by_user_date(user, date).template

    # We should make this guy atomic:
    RECORDS.delete_by_user_date(user, date)

    # We should validate somet of this stuffs! Like the total count and the buckets being in
    # the template!

    buckets = request.get_json()['buckets']

    total_tokens = sum([x['tokens'] for x in buckets])
    if total_tokens > template.template['maxTokens']:
        return 'Too many tokens submitted; maximum is %s' % template.template['maxTokens'], 403

    template_buckets = [x['bucket'] for x in template.template['buckets']]
    for allocation in buckets:
        if allocation['bucket'] not in template_buckets:
            return '%s is not a valid bucket' % allocation['bucket'], 403
        record = Record(user=user,
                        date=date,
                        template=template,
                        code=allocation['bucket'],
                        tokens=allocation['tokens'])

        RECORDS.create(record)

    return jsonify({'date': date,
                    'template': template._asdict(),
                    'buckets': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                for x in RECORDS.fetch_by_user_date(user, date)]})

@app.route("/<string:username>/tokens/<date:date>", methods=['GET'])
def get_tokens(username, date):
    user = USERS.fetch_by_username(username)
    template = ASSOCIATIONS.fetch_by_user_date(user, date).template

    return jsonify({'date': date,
                    'template': template._asdict(),
                    'buckets': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                for x in RECORDS.fetch_by_user_date(user, date)]})
