"""Custom JSON Encoder"""
from flask.json import JSONEncoder
from spudbin.app.api.Reports import JSDate

class CustomJSONEncoder(JSONEncoder):
    """Custom JSON encoder replaceing JSDates (a custom type created specifically for this
    purpose) into dates that Google Charts wants to see"""

    def default(self, obj): # pylint: disable=E0202
        try:
            if isinstance(obj, JSDate):
                return 'Date(%d, %d, %d)' % (obj.date.year, obj.date.month - 1, obj.date.day)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
