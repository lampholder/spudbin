import datetime

from functools import wraps

from flask import jsonify
from flask import request

import requests

from spudbin.app import app
from spudbin.app import config
from spudbin.app import admins

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
    """Checks that the user is allowed to do what they're trying to do. Very simple perms model -
    either you're doing an action to yourself, or you're an admin."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """Wrapper function, obvs"""
        if 'username' in kwargs:
            doer = request.headers.get('Github-Login')
            doee = kwargs['username']
            if doer != doee and doer not in admins:
                # Very simplistic authorisation model right now
                return 'The person you\'re claiming to be isn\'t allowed to do this', 403
        return func(*args, **kwargs)
    return wrapped

def admin_only(func):
    """Checks that the username is in the admin set - must always be used in conjunction
    with @authenticated else it's useless."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        "Wrapper function, obvs"""
        doer = request.headers.get('Github-Login')
        if doer not in admins:
            return 'The person you\'re claiming to be isn\'t allowed to do this', 403
        return func(*args, **kwargs)
    return wrapped

# Templates:
@app.route(config.get('interface', 'application_root') + '/api/templates', methods=['GET'])
@authenticated
@admin_only
def get_templates():
    with Database.connection() as connection:
        return jsonify([x._asdict() for x in TEMPLATES.all(connection)])

@app.route(config.get('interface', 'application_root') + "/api/templates", methods=['POST'])
@authenticated
@admin_only
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

@app.route(config.get('interface', 'application_root') + "/api/templates/<int:template_id>", methods=['GET'])
@authenticated
def get_template_by_id(template_id):
    with Database.connection() as connection:
        return jsonify(TEMPLATES.fetch_by_pkey(template_id, connection)._asdict())

# User templates:
@app.route(config.get('interface', 'application_root') + '/api/<string:username>/templates', methods=['GET'])
@authenticated
@authorised
def get_templates_for_user(username):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        #TODO: This chap only _asdict()ifies the first entity - all the children remain namedtuples
        # and lose their keys :(
        return jsonify([filter_keys(x._asdict(), ['user'])
                        for x in ASSOCIATIONS.fetch_by_user(user, connection)])

@app.route(config.get('interface', 'application_root') + '/api/<string:username>/templates/<int:template_id>', methods=['POST'])
@authenticated
@authorised
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

@app.route(config.get('interface', 'application_root') + "/api/<string:username>/templates/<date:date>", methods=['GET'])
@authenticated
@authorised
def get_template_by_user_date(username, date):
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        association = ASSOCIATIONS.fetch_by_user_date(user, date, connection)
        return jsonify(association.template._asdict())

@app.route(config.get('interface', 'application_root') + "/api/<string:username>/tokens/<date:date>", methods=['POST'])
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

@app.route(config.get('interface', 'application_root') + "/api/<string:username>/tokens/<date:date>", methods=['GET'])
@authenticated
@authorised
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

@app.route(config.get('interface', 'application_root') + '/api/reports/<string:username>', methods=['GET'])
def get_stats(username):
    """Fetch the aggregated stats over a period."""
    from collections import defaultdict
    data = defaultdict(int)
    total = 0

    def simplify_record(record):
        tags = [bucket for bucket in record.template.buckets
                if bucket['bucket'] == record.bucket][0]['tags']
        return (record.bucket, record.tokens, tags)

    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)
        start = datetime.datetime.strptime(request.args.get('start'), '%Y-%m-%d')
        end = datetime.datetime.strptime(request.args.get('end'), '%Y-%m-%d')
        group_by = request.args.get('groupBy')
        time_window = request.args.get('timeWindow')

        record_list = {}
        for date in [start + datetime.timedelta(n) for n in range((end - start).days)]:
            records = RECORDS.fetch_by_user_date(user, date, connection)
            record_list[date] = records

        slyces = defaultdict(list)
        for date, records in record_list.iteritems():
            if time_window == 'week':
                slyces[date.isocalendar()[1]] += [simplify_record(record) for record in records]
            elif time_window == 'month':
                slyces[date.month] += [simplify_record(record) for record in records]

        return jsonify(slyces)
#        for slyce, record_list in slyces:
#            for record in records:
#                total += record.tokens
#                if group_by == 'bucket':
#                    data[record.bucket] = 0
#                    data[record.bucket] += record.tokens
#                elif group_by == 'tag':
#                    tags = [bucket for bucket in record.template.buckets
#                            if bucket['bucket'] == record.bucket][0]['tags']
#                    for tag in tags:
#                        data[tag] += record.tokens
#        return jsonify({'data': data, 'total': total})



