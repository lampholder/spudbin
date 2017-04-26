from flask import Flask
from flask import jsonify
from flask import redirect
from flask import request

import requests
import uuid

from datetime import datetime
from werkzeug.routing import BaseConverter, ValidationError

class DateConverter(BaseConverter):
    """Extracts a ISO8601 date from the path and validates it."""

    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')

app.url_map.converters['date'] = DateConverter

@app.route("/template/<string:user>/<date:date>", methods=['GET'])
def get_template(user, date):
    return jsonify(user=user,
                   date=date,
                   template={'id': 1,
                             'buckets':[{'bucket': 'working', 'tags': ['good'], 'description': 'working hard, yeah'},
                                        {'bucket': 'slacking', 'tags': ['bad'], 'description': 'mooching around, wasting time'}]
                            }
                  )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
