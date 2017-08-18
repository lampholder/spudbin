"""Stop losing this link: https://developers.google.com/chart/interactive/docs/reference"""

import datetime

from collections import defaultdict
from collections import namedtuple

from flask import jsonify
from flask import request

from spudbin.app import app
from spudbin.app import config

from spudbin.util import JSDate

from spudbin.storage import Database
from spudbin.storage import Users
from spudbin.storage import Templates
from spudbin.storage import Records
from spudbin.storage import Associations

CONNECTION = Database.connection()

USERS = Users()
TEMPLATES = Templates()
ASSOCIATIONS = Associations()
RECORDS = Records()

SimplifiedRecord = namedtuple('SimplifiedRecord', ['bucket', 'tags', 'tokens'])

def simplify_record(record):
    """Create an object that's simpler to reason about."""
    tags = [bucket for bucket in record.template.buckets
            if bucket['bucket'] == record.bucket][0]['tags']
    return SimplifiedRecord(bucket=record.bucket,
                            tags=tags,
                            tokens=record.tokens)

def fetch_simplified_records_for_period(usernames, start, end):
    """Returns a dict of dates to arrays of records."""
    with Database.connection() as connection:
        # Fetch all of the tokens for each day in the period.
        record_list = {}
        for username in usernames:
            user = USERS.fetch_by_username(username, connection)

            for date in [start + datetime.timedelta(n) for n in range((end - start).days)]:
                records = RECORDS.fetch_by_user_date(user, date, connection)
                record_list[date] = [simplify_record(record) for record in records]

        return record_list

def get_buckets(records_list):
    """Distills the full results set into a set of buckets"""
    buckets = set()
    for _, records in records_list.iteritems():
        for record in records:
            buckets.add(record.bucket)
    return buckets

def get_tags(records_list):
    """Distills the full results set into a set of tags"""
    tags = set()
    for _, records in records_list.iteritems():
        for record in records:
            for tag in record.tags:
                tags.add(tag)
    return tags

@app.route(config.get('interface', 'application_root') + '/api/reports/whoHasTokenized', methods=['GET'])
def get_who_has_tokenized():
    """Fetch a list of days and who has completed their tokens for those days."""
    start = datetime.datetime.strptime(request.args.get('start'), '%Y-%m-%d')
    end = datetime.datetime.strptime(request.args.get('end'), '%Y-%m-%d')

    usernames = request.args.get('usernames').split(',')

    cols = [{'label': 'date', 'type': 'date'}]
    cols += [{'label': x, 'type': 'string'} for x in usernames]
    rows = []

    with Database.connection() as connection:
        weekend = set([5, 6])
        for date in [start + datetime.timedelta(n) for n in range((end - start).days)]:
            if date.weekday() in weekend:
                continue
            cells = [{'v': JSDate(date)}]
            for username in usernames:
                # FIXME: This is inefficient.
                user = USERS.fetch_by_username(username, connection)
                records = [simplify_record(x)
                           for x in RECORDS.fetch_by_user_date(user, date, connection)]
                total = sum([x.tokens for x in records])
                cells.append({'v': total})
            rows.append({'c': cells})

        return jsonify({'cols': cols,
                        'rows': rows})


@app.route(config.get('interface', 'application_root') + '/api/reports', methods=['GET'])
def get_stats():
    """Fetch the aggregated stats over a period."""
    # FIXME: This method is a beast.
    start = datetime.datetime.strptime(request.args.get('start'), '%Y-%m-%d')
    end = datetime.datetime.strptime(request.args.get('end'), '%Y-%m-%d')

    group_by = request.args.get('groupBy')
    if group_by not in ('tag', 'bucket'):
        return jsonify({'error':
                        'Invalid groupBy setting; should be either \'tag\' or \'bucket\''}), 400

    time_window = request.args.get('timeWindow')
    if time_window not in ('week', 'month', 'period'):
        return jsonify({'error':
                        ('Invalid timeWindow setting; ' +
                         'should be either \'week\', \'month\' or \'period\'')}), 400

    tags_to_filter = request.args.get('tags').split(',') if request.args.get('tags') else None

    usernames = request.args.get('usernames').split(',') if request.args.get('usernames') else None

    # Fetch the data from the db
    records_list = fetch_simplified_records_for_period(usernames, start, end)

    # Set up the data table columns
    cols = [{'label': 'date', 'type': 'date'}]
    if group_by == 'tag':
        groups = get_tags(records_list)
        if tags_to_filter is not None:
            groups = [group for group in groups if group in tags_to_filter]
    else:
        groups = get_buckets(records_list)

    for group in groups:
        cols.append({'label': group, 'type': 'number'})

    # Slice the data by period
    period = 'period'
    period_map = lambda x: JSDate(start)

    if time_window == 'week':
        period = 'week'
        period_map = lambda x: JSDate(datetime.datetime.strptime('%s-W%s-1' %
                                                                 (x.year, x.isocalendar()[1]),
                                                                 '%Y-W%W-%w').date())
    elif time_window == 'month':
        period = 'month'
        period_map = lambda x: JSDate(datetime.date(x.year, x.month, 1))

    periods = defaultdict(list)
    for date, records in records_list.iteritems():
        periods[period_map(date)] += records

    rows = []
    for period, records in periods.iteritems():
        tokens = defaultdict(lambda: 0)
        for record in records:
            if group_by == 'bucket':
                # Bucket doesn't implement tags_to_filter - is that okay?
                tokens[record.bucket] += record.tokens
            elif group_by == 'tag':
                for tag in record.tags:
                    if tags_to_filter is None or tag in tags_to_filter:
                        tokens[tag] += record.tokens

        cells = [{'v': period}]
        for group in groups:
            if group in tokens:
                cells.append({'v': tokens[group]})
            else:
                cells.append(None)
        rows.append({'c': cells})

    return jsonify({'cols': cols, 'rows': rows})
