import datetime

from functools import wraps

from flask import jsonify
from flask import request
from flask import session
from flask import redirect

import requests

from spudbin.app import app

from spudbin.storage import Database
from spudbin.storage import Users
from spudbin.storage import Templates, Template
from spudbin.storage import Records, Record
from spudbin.storage import Associations, Association

CONNECTION = Database.connection()

USERS = Users()
TEMPLATES = Templates()
ASSOCIATIONS = Associations()
RECORDS = Records()

def filter_keys(dic, keys):
    filtered = dict(dic)
    for key in keys:
        if key in filtered:
            del filtered[key]
    return filtered

# Templates:
@app.route('/templates', methods=['GET'])
def get_templates():
    with Database.connection() as connection:
        return jsonify([x._asdict() for x in TEMPLATES.all(connection)])

@app.route("/templates", methods=['POST'])
def create_template():
    """Upload a new template"""
    with Database.connection() as connection:
        if not Templates.validate_json_template(request.get_json()):
            return 'Invalid template object', 400
        row_id = TEMPLATES.create(Template(pkey=None,
                                           template=request.get_json(),
                                           enabled=True),
                                  connection)
        connection.commit()
        return jsonify(TEMPLATES.fetch_by_pkey(row_id, connection)._asdict())

@app.route("/templates/<int:template_id>", methods=['GET'])
def get_template_by_id(template_id):
    with Database.connection() as connection:
        return jsonify(TEMPLATES.fetch_by_pkey(template_id, connection)._asdict())


def is_authed(username):
    if 'github_token' not in session:
        return False
    with Database.connection() as connection:
        users = USERS.fetch_by_username(username, connection)
    if users is None:
        return False #XXX: Gotta do better than this
    auth_test = requests.get('https://api.github.com/user',
                             params={'access_token': session['github_token']})
    return auth_test.status_code != 200

def authenticate(username):
    if not is_authed(username):
        return redirect('https://spudb.in/login', code='302')

def authed(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        print 'Calling a cool wrapped function'
        return 'werp' #func(*args, **kwargs)
    return wrapped


# User templates:
@authed
@app.route('/<string:username>/templates', methods=['GET'])
def get_templates_for_user(username):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        return jsonify([filter_keys(x._asdict(), ['user'])
                        for x in ASSOCIATIONS.fetch_by_user(user, connection)])

@app.route('/<string:username>/templates/<int:template_id>', methods=['POST'])
def assign_template_for_user(username, template_id):
    with Database.connection() as connection:
        start_date = datetime.datetime.strptime(request.get_json()['startDate'], '%Y-%m-%d').date()
        user = USERS.fetch_by_username(username, connection)
        template = TEMPLATES.fetch_by_pkey(template_id, connection)

        ASSOCIATIONS.create(Association(pkey=None,
                                        user=user,
                                        template=template,
                                        start_date=start_date,
                                        end_date=None),
                            connection)
        connection.commit()
        return 'OKAY', 200

@app.route("/<string:username>/templates/<date:date>", methods=['GET'])
def get_template_by_user_date(username, date):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        association = ASSOCIATIONS.fetch_by_user_date(user, date, connection)
        return jsonify(association.template._asdict())

@app.route("/<string:username>/tokens/<date:date>", methods=['POST'])
def submit_tokens(username, date):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        template = ASSOCIATIONS.fetch_by_user_date(user, date, connection).template

        RECORDS.delete_by_user_date(user, date, connection)

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

            RECORDS.create(record, connection)

        connection.commit()

        return jsonify({'date': date,
                        'template': template._asdict(),
                        'buckets': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                    for x in RECORDS.fetch_by_user_date(user, date, connection)]})

@app.route("/<string:username>/tokens/<date:date>", methods=['GET'])
def get_tokens(username, date):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        tokens = RECORDS.fetch_by_user_date(user, date, connection)

        template_pkeys = list(set([x.template.pkey for x in tokens]))
        if len(template_pkeys) == 0:
            return '{}', 200
        elif len(template_pkeys) > 1:
            return 'ZOMG tokens filed for multiple templates on the same day D:', 500

        template = TEMPLATES.fetch_by_pkey(template_pkeys[0], connection)

        return jsonify({'date': date,
                        'template': template._asdict(),
                        'tokens': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                   for x in tokens]})
