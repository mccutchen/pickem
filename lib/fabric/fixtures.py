from __future__ import with_statement

import logging
import datetime
import os
import sys
import time

from django.utils import simplejson as json
from google.appengine.ext import db


DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

def json_encoder(obj):
    """Objects are encoded as one-item dictionaries mapping '__TYPENAME__' to
    a serializable representation of the type."""
    if isinstance(obj, datetime.datetime):
        return { '__datetime__': obj.strftime(DATETIME_FORMAT) }
    elif isinstance(obj, datetime.date):
        return { '__date__': obj.strftime(DATE_FORMAT) }
    return obj

def json_decoder(dct):
    """Decodes objects encoded as one-item dictionaries. See json_encoder."""
    if len(dct) == 1:
        type_name, value = dct.items()[0]
        type_name = type_name.strip('_')
        if type_name == 'datetime':
            return datetime.datetime.strptime(value, DATETIME_FORMAT)
        elif type_name == 'date':
            return datetime.datetime.strptime(value, DATE_FORMAT).date()
    return dct


def load_fixtures(filename):
    """Loads fixtures from the given path into the datastore."""
    logging.info("Loading fixtures from %s..." % os.path.basename(filename))

    with open(filename, 'r') as f:
        json_obj = json.load(f, object_hook=json_decoder)

    for count, data in enumerate(json_obj):
        model = get_model(data['model'])
        if model is None:
            return

        parent = make_parent_key(data.get('parent'))
        key = make_key(model, data.get('key'), parent=parent)
        create_entity(model, key, data['fields'], filename)

    logging.info("Loaded %d fixtures..." % (count + 1))

def get_model(modelspec):
    """Gets the model class specified in the given modelspec, which should
    be in the format `path.to.models.module.ModelName`."""
    module_name, model = modelspec.rsplit('.', 1)
    try:
        __import__(module_name, {}, {})
    except ImportError, e:
        logging.error('Could not import module for %s' % modelspec)
        return None
    else:
        module = sys.modules[module_name]
        try:
            return getattr(module, model)
        except AttributeError, e:
            logging.error('Could not find model for %s' % modelspec)
            return None

def make_parent_key(parentspec):
    """Creates a parent key from the given key spec, which should be a
    two-item iterable of (modelspec, keydata) specifying the parent model and
    key."""
    if parentspec is None:
        return None
    try:
        modelspec, keydata = parentspec
    except ValueError:
        logging.error('Invalid parent spec: %r' % parentspec)
        return None
    else:
        model = get_model(modelspec)
        if model:
            return make_key(model, keydata)
        else:
            logging.error('Could not find parent model: %s' % modelspec)
            return None

def make_key(model, keydata, parent=None):
    """Creates a datastore key for the given model with the given key data,
    which can be an ID or a string."""
    if keydata is None:
        return None
    else:
        return db.Key.from_path(model.kind(), keydata, parent=parent)

def create_entity(model, key, fields, fixture_path):
    """Creates an entity of the given type in the datastore, based on the
    given fields.  ReferenceProperties and ListProperties are containing Keys
    are looked up in the datastore."""

    logging.debug('Creating %s entity with key %r' % (model.kind(), key))

    # The final keyword argument we'll pass to the entity's constructor
    args = { 'key': key }

    for field, value in fields.iteritems():
        # What kind of property does this field need to be?
        prop = getattr(model, field)

        # If it's a ReferenceProperty, look it up in the datastore based on
        # the serialized filter values
        if isinstance(prop, db.ReferenceProperty):
            logging.error('Reference properties not handled')
            raise RuntimeError
            value = lookup_entity(prop.reference_class, *value)

        # If it's a ListProperty containing Keys, look up each element in the
        # list based on the filter values specified
        elif isinstance(prop, db.ListProperty) and prop.item_type == db.Key:
            logging.error('Lists of keys not handled')
            raise RuntimeError

        # If it's a BlobProperty, treat the value as a path, relative to the
        # current fixture, that contains the data for the property
        elif isinstance(prop, db.BlobProperty):
            if value:
                blob_path = os.path.join(os.path.dirname(fixture_path), value)
                value = open(blob_path, 'rb').read()

        # Otherwise, assume that the type resulting from JSON deserialization
        # is appropriate for the datastore
        args[str(field)] = value

    # Create and store the entity
    model(**args).put()

def lookup_entity(model, property_operator=None, value=None):
    """Looks up an entity of the given type by filtering on the given property
    and value (which latter two arguments are passed directly on to the
    Query.filter() method."""

    if None in (property_operator, value):
        raise ValueError, """Entity references must be specified as a sequence
 of two items suitable for use as the args to Query.filter()"""

    if property_operator == "key_name":
        q = None
        entity = model.get_by_key_name(value)
    elif property_operator == 'id':
        q = None
        entity = model.get_by_id(value)
    else:
        q = model.all().filter(property_operator, value)
        entity = q.get()

    if entity is None:
        raise ValueError, '%s not found for filter %s %s' % (
            model, property_operator.strip(), value)
    elif q and q.count() > 1:
        raise ValueError, 'Multiple %s instances found for filter %s %s' % (
            model, property_operator.strip(), value)
    return entity

def serialize_entities(modelspec):
    model = get_model(modelspec)
    fields = model.properties()
    entities = []
    for entity in model.all():
        d = {
            'model': modelspec,
            'key': entity.key().id_or_name(),
            }

        parent_key = entity.parent_key()
        if parent_key:
            d['parent'] = make_keyspec(entity.parent())

        d['fields'] = {}
        for name, kind in fields.items():
            value = getattr(entity, name)
            if isinstance(kind, db.ReferenceProperty):
                value = make_keyspec(value)
            elif isinstance(kind, db.ListProperty) \
                    and kind.item_type == db.Key:
                items = db.get(value)
                value = map(make_keyspec, db.get(value))
            d['fields'][name] = value

        entities.append(d)

    return json.dumps(entities, default=json_encoder, indent=4)

def make_keyspec(entity):
    return ['%s.%s' % (entity.__module__, entity.kind()),
            entity.key().id_or_name()]
