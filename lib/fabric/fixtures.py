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
    elif isinstance(obj, db.Key):
        return {
            '__key__': [
                obj.kind(),
                obj.id_or_name(),
                json_encoder(obj.parent())
                ]
            }
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
        elif type_name == 'key':
            kind, keydata, parent = value
            return db.Key.from_path(kind, keydata, parent=parent)
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
        create_entity(model, data.get('key'), data['fields'], filename)
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
            value = db.get(value)

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

def serialize_entities(modelspec):
    model = get_model(modelspec)
    fields = model.properties()
    entities = []
    for entity in model.all():
        d = {
            'model': modelspec,
            'key': entity.key(),
            }

        d['fields'] = {}
        for name, kind in fields.items():
            value = getattr(entity, name)
            if isinstance(kind, db.ReferenceProperty):
                value = value.key()
            d['fields'][name] = value

        entities.append(d)

    return json.dumps(entities, default=json_encoder, indent=4)
