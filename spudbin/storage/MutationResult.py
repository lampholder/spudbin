"""Class for returning the results of any create or update operation."""
class MutationResult(object):
    """Class for returning the results of any create or update operation."""

    def __init__(self, cursor):
        self.lastrowid = cursor.lastrowid
        self._cursor = cursor
        self._connection = cursor.connection

    def commit(self):
        """Commit the changes."""
        self._connection.commit()
        return self

    def close_cursor(self):
        """Close the cursor."""
        self._cursor.close()
        return self
