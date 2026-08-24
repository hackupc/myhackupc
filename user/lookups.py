import unicodedata

from django.db.backends.signals import connection_created
from django.db.models import CharField, TextField, Transform


def strip_accents(value):
    if value is None:
        return None
    return ''.join(char for char in unicodedata.normalize('NFKD', value) if not unicodedata.combining(char))


class Unaccent(Transform):
    bilateral = True
    lookup_name = 'unaccent'
    function = 'UNACCENT'


def register_sqlite_unaccent(connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_function('unaccent', 1, strip_accents, deterministic=True)


def register():
    CharField.register_lookup(Unaccent)
    TextField.register_lookup(Unaccent)
    connection_created.connect(register_sqlite_unaccent)
