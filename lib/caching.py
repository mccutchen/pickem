"""
Some code written by Nick Johnson of Google to help cache lists of models.
"""

import logging
from binascii import b2a_base64 as b2a, a2b_base64 as a2b

from google.appengine.ext import db
from google.appengine.datastore import entity_pb
from google.appengine.api import memcache


def serialize_models(models):
    """Serialize a list of models efficiently for memcached."""
    if models is None:
        return None
    elif isinstance(models, db.Model):
        return db.model_to_protobuf(models).Encode()
    else:
        return [db.model_to_protobuf(x).Encode() for x in models]

def deserialize_models(data):
    """Deserialize a list of models efficiently for memcached."""
    if data is None:
        return None
    elif isinstance(data, str):
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x))
                for x in data]

def cachemodel(key, model, **kwargs):
    """Serializes the given model or models and caches them under the given
    key. If key is a list, model should be an equal-length list.  Keyword args
    are passed on to memcache."""
    data = serialize_models(model)
    if isinstance(key, (list, tuple)):
        to_cache = dict((k, v) for k, v in zip(key, data))
        try:
            return memcache.set_multi(to_cache, **kwargs)
        except Exception, e:
            logging.error('cachemodel: memcache.set_multi(%r) failed' % key)
            return False
    else:
        try:
            return memcache.set(key, data, **kwargs)
        except Exception, e:
            logging.error('cachemodel: memcache.set(%r) failed' % key)
            return False

def uncachemodel(key, **kwargs):
    """Tries to retrieve the specified value from the cache.  If found, it is
    assumed to be a cached model and will be deserialized.  If key is a list,
    a dictionary will be returned.  Keyword args are passed on to memcache."""
    if isinstance(key, (list, tuple)):
        try:
            data = memcache.get_multi(key, **kwargs)
        except Exception, e:
            logging.error('uncachemodel: memcache.get_multi(%r) failed' % key)
            return None
        else:
            return dict((k,deserialize_models(v)) for k,v in data.iteritems())
    else:
        try:
            return deserialize_models(memcache.get(key, **kwargs))
        except Exception, e:
            logging.error('uncachemodel: memcache.get(%r) failed' % key)
            return None
