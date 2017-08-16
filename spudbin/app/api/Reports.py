import datetime

from collections import defaultdict
from collections import namedtuple

from flask import jsonify
from flask import request

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

SimplifiedRecord = namedtuple('SimplifiedRecord', ['bucket', 'tags', 'tokens'])

def simplify_record(record):
    tags = [bucket for bucket in record.template.buckets
            if bucket['bucket'] == record.bucket][0]['tags']
    return SimplifiedRecord(bucket=record.bucket,
                            tags=tags,
                            tokens=record.tokens)

def fetch_simplified_records_for_period(username, start, end):
    """Returns a dict of dates to arrays of records."""
    with Database.connection() as connection:
        user = USERS.fetch_by_username(username, connection)

        # Fetch all of the tokens for each day in the period.
        record_list = {}
        for date in [start + datetime.timedelta(n) for n in range((end - start).days)]:
            records = RECORDS.fetch_by_user_date(user, date, connection)
            record_list[date] = [simplify_record(record) for record in records]

        return record_list

def get_buckets(records_list):
    buckets = set()
    for date, records in records_list.iteritems():
        for record in records:
            buckets.add(record.bucket)
    return buckets

def get_tags(records_list):
    tags = set()
    for date, records in records_list.iteritems():
        for record in records:
            for tag in record.tags:
                tags.add(tag)
    return tags

@app.route(config.get('interface', 'application_root') + '/api/reports/<string:username>', methods=['GET'])
def get_stats(username):
    """Fetch the aggregated stats over a period."""
    start = datetime.datetime.strptime(request.args.get('start'), '%Y-%m-%d')
    end = datetime.datetime.strptime(request.args.get('end'), '%Y-%m-%d')

    group_by = request.args.get('groupBy')
    if group_by not in ('tag', 'bucket'):
        return jsonify({'error': 'Invalid groupBy setting; should be either \'tag\' or \'bucket\''}), 400

    time_window = request.args.get('timeWindow')
    if time_window not in ('week', 'month', 'period'):
        return jsonify({'error': 
                        'Invalid timeWindow setting; should be either \'week\', \'month\' or \'period\''}), 400

    # Fetch the data from the db
    records_list = fetch_simplified_records_for_period(username, start, end)

    # Set up the data table columns
    cols = [{'label': 'week', 'type': 'number'}]
    if group_by == 'tag':
        groups = get_tags(records_list)
    else:
        groups = get_buckets(records_list)

    for group in groups:
        cols.append({'label': group, 'type': 'number'})

    # Slice the data by period
    period = 'period'
    period_map = lambda x: -1

    if time_window == 'week':
        period = 'week'
        period_map = lambda x: x.isocalendar()[1]
    elif time_window == 'month':
        period = 'month'
        period_map = lambda x: x.month

    periods = defaultdict(list)
    for date, records in records_list.iteritems():
        periods[period_map(date)] += records


    import json
    rows = []
    for period, records in periods.iteritems():
        tokens = defaultdict(lambda: 0)
        for record in records:
            if group_by == 'bucket':
                tokens[record.bucket] += record.tokens
            elif group_by == 'tag':
                for tag in record.tags:
                    tokens[tag] += record.tokens 

        cells = [{'v': period}]
        for group in groups:
            if group in tokens:
                cells.append({'v': tokens[group]})
            else:
                cells.append(None)
        rows.append({'c': cells})

    return jsonify({'cols': cols, 'rows': rows})
