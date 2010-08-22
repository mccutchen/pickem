import logging
from functools import wraps

from webob.exc import HTTPNotFound
from google.appengine.ext import db

import models


def pool_required(meth):
    @wraps(meth)
    def decorated_meth(self, pool_id, *args, **kwargs):
        try:
            pool = models.Pool.get_by_id(int(pool_id))
        except:
            pool = None
        if pool is None:
            raise HTTPNotFound('Pool %s not found' % pool_id)
        else:
            return meth(self, pool, *args, **kwargs)
    return decorated_meth

def entry_required(meth):
    @wraps(meth)
    def decorated_meth(self, pool_id, entry_id, *args, **kwargs):
        pool_key = db.Key.from_path('Pool', int(pool_id))
        entry_key = db.Key.from_path('Entry', int(entry_id), parent=pool_key)
        try:
            pool, entry = db.get([pool_key, entry_key])
        except:
            pool, entry = None, None
        if None in (pool, entry):
            raise HTTPNotFound('Pool %s not found' % pool_id)
        else:
            return meth(self, pool, entry, *args, **kwargs)
    return decorated_meth
