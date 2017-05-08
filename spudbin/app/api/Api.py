import datetime

from functools import wraps

from flask import jsonify
from flask import request

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
    #TODO: Replace all usage of this with a standard dict comprehension
    filtered = dict(dic)
    for key in keys:
        if key in filtered:
            del filtered[key]
    return filtered

# Auth decorators
def authenticated(func):
    """Only checks that this person is who they say they are"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """Wrapper function, obvs"""
        username = request.headers.get('Github-Login')
        token = request.headers.get('Github-Auth-Token')

        auth_test = requests.get('https://api.github.com/user',
                                 params={'access_token': token})

        is_authed = (auth_test.status_code == 200 and
                     'login' in auth_test.json() and
                     auth_test.json()['login'] == username)
        if not is_authed:
            return 'I don\'t know who you are, or I don\'t believe you are ' + \
                   'who you say you are.', 401
        return func(*args, **kwargs)
    return wrapped

def authorised(func):
    """Checks that the user is allowed to do what they're trying to do."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """Wrapper function, obvs"""
        if 'username' in kwargs:
            doer = request.headers.get('Github-Login')
            doee = kwargs['username']
            if doer != doee:
                # Very simplistic authorisation model right now
                return 'The person you\'re claiming to be isn\'t allowed to do this', 403
        return func(*args, **kwargs)
    return wrapped

# Templates:
@app.route('/api/templates', methods=['GET'])
def get_templates():
    with Database.connection() as connection:
        return jsonify([x._asdict() for x in TEMPLATES.all(connection)])

@app.route("/api/templates", methods=['POST'])
def create_template():
    """Upload a new template"""
    with Database.connection() as connection:
        template = request.get_json()
        if not Templates.validate_json_template(template):
            return 'Invalid template object', 400
        row_id = TEMPLATES.create(Template(pkey=None,
                                           maxTokens=template['maxTokens'],
                                           buckets=template['buckets'],
                                           layout=template.get('layout', None),
                                           enabled=True),
                                  connection)
        connection.commit()
        return jsonify(TEMPLATES.fetch_by_pkey(row_id, connection)._asdict())

@app.route("/api/templates/<int:template_id>", methods=['GET'])
def get_template_by_id(template_id):
    with Database.connection() as connection:
        return jsonify(TEMPLATES.fetch_by_pkey(template_id, connection)._asdict())

# User templates:
@app.route('/api/<string:username>/templates', methods=['GET'])
def get_templates_for_user(username):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        #TODO: This chap only _asdict()ifies the first entity - all the children remain namedtuples
        # and lose their keys :(
        return jsonify([filter_keys(x._asdict(), ['user'])
                        for x in ASSOCIATIONS.fetch_by_user(user, connection)])

@app.route('/api/<string:username>/templates/<int:template_id>', methods=['POST'])
def assign_template_for_user(username, template_id):
    with Database.connection() as connection:
        start_date = datetime.datetime.strptime(request.get_json()['startDate'], '%Y-%m-%d').date()
        user = USERS.fetch_by_username(username, connection)
        template = TEMPLATES.fetch_by_pkey(template_id, connection)

        ASSOCIATIONS.create(Association(pkey=None,
                                        user=user,
                                        template=template,
                                        start_date=start_date,
                                        #TODO: something better here.
                                        end_date=datetime.datetime.strptime('9000-01-01', '%Y-%m-%d')),
                            connection)
        connection.commit()
        return jsonify({'result': 'success',
                        'message': 'Template assigned successfully'})

@app.route("/api/<string:username>/templates/<date:date>", methods=['GET'])
def get_template_by_user_date(username, date):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        association = ASSOCIATIONS.fetch_by_user_date(user, date, connection)
        return jsonify(association.template._asdict())

@app.route("/api/<string:username>/tokens/<date:date>", methods=['POST'])
@authenticated
@authorised
def submit_tokens(username, date):
    """Submit tokens for a given day; they are automatically associated with the
    current active template."""
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        template = ASSOCIATIONS.fetch_by_user_date(user, date, connection).template

        buckets = request.get_json()['buckets']

        total_tokens = sum([x['tokens'] for x in buckets])
        if total_tokens > template.maxTokens:
            return 'Too many tokens submitted; maximum is %s' % template.maxTokens, 403

        RECORDS.delete_by_user_date(user, date, connection)

        template_buckets = [x['bucket'] for x in template.buckets]
        for allocation in buckets:
            if allocation['bucket'] not in template_buckets:
                return '%s is not a valid bucket' % allocation['bucket'], 403
            record = Record(user=user,
                            date=date,
                            template=template,
                            bucket=allocation['bucket'],
                            tokens=allocation['tokens'])

            RECORDS.create(record, connection)

        return jsonify({'date': date,
                        'template': template._asdict(),
                        'buckets': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                    for x in RECORDS.fetch_by_user_date(user, date, connection)]})

@app.route("/api/<string:username>/tokens/<date:date>", methods=['GET'])
def get_tokens(username, date):
    """Fetch the tokens submitted for a given day, plus the template against which they
    were submitted."""
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        tokens = RECORDS.fetch_by_user_date(user, date, connection)

        template_pkeys = list(set([x.template.pkey for x in tokens]))
        if len(template_pkeys) == 0:
            return '{}', 404
        elif len(template_pkeys) > 1:
            return jsonify({'result': 'error',
                            'message': 'ZOMG tokens filed for multiple templates on the same day D:'}), 500

        template = TEMPLATES.fetch_by_pkey(template_pkeys[0], connection)

        return jsonify({'date': date,
                        'template': template._asdict(),
                        'tokens': [filter_keys(x._asdict(), ['user', 'template', 'date'])
                                   for x in tokens]})
