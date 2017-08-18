class JSDate(object):
    """Flask's Jsonify can have specific obj->json mapping impls specified on a
    type-by-type basis only. For that reason, the report code is wrapping dates
    in a JSDate class so that only the JSDate dates will be mapped to the
    "Date(2010, 10, 0)" format required by Google Charts. Everything else can
    remain in 2010-10-01 format unmolested."""

    def __init__(self, date):
        self.date = date

    def __eq__(self, other):
        return self.date == other.date

    def __hash__(self):
        return hash(self.date)

