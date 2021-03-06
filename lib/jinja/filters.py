import datetime
import logging
import re

from django.template.defaultfilters import pluralize, timeuntil, floatformat

def est(d):
    """Converts the given datetime or date object from UTC to EST. Used to
    display game kickoff times."""
    return d + datetime.timedelta(hours=-5)

def date(d, format):
    """Formats the given datetime object according to the given format string.
    If `fix` is True, the time will automatically be adjusted to from UTC to
    Eastern Standard Time. Leading zeros will be removed from numbers in the
    results."""
    result = d.strftime(format)
    return re.sub(r'0(\d.\d{2})', r'\1', result)

def key(obj):
    """Returns the given object's datastore key, if it has one. Otherwise,
    returns the object itself."""
    try:
        return obj.key()
    except AttributeError:
        return obj

def id(obj):
    """Returns the given object's datastore key's id or name, if it has
    one. Otherwise, returns the object itself."""
    try:
        return key(obj).id_or_name()
    except AttributeError:
        return obj
