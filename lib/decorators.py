import logging
from functools import wraps

from webob.exc import HTTPNotFound, HTTPBadRequest
from google.appengine.ext import db

import models


def objects_required(*kinds):
    """A view method decorator takes care of retrieving the given kinds of
    objects from the datastore and ensuring that they exist.  Makes some heavy
    assumptions about the decorated method and the objects in question:

     - The first len(kinds) arguments to the view method are key IDs (if
       they're numeric) or names that can be used to retrieve the
       corresponding kind.

     - If more than one kind is specified, each subsequent kind is a child of
       the previous one.

    So, given a route like:

        /people/(\w+)

    and a request to:

        /people/jimmy

    that maps to a view method like:

        @objects_required('Person')
        def get(self, person):
            pass

    this decorator will take care of looking up the Person object with a key
    name of "jimmy" and ensuring that it exists before passing it on to the
    view method.
    """
    def real_decorator(meth):
        @wraps(meth)
        def decorated_meth(self, *args, **kwargs):
            if len(args) < len(kinds):
                raise HTTPBadRequest('Expected at least %s args' % len(kinds))
            kinds_ids = zip(kinds, args)
            parent_key = None
            keys = []
            for i, (kind, id) in enumerate(kinds_ids):
                if id.isdigit():
                    id = int(id)
                key = db.Key.from_path(kind, id, parent=parent_key)
                parent_key = key
                keys.append(key)
            try:
                objs = db.get(keys)
            except:
                objs = [None]
            if not all(objs):
                raise HTTPNotFound
            else:
                new_args = objs + list(args[len(kinds):])
                return meth(self, *new_args, **kwargs)
        return decorated_meth
    return real_decorator
