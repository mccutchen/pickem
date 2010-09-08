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
        # Keys are encoded as a 3-element list of [kind, id_or_name, parent]
        # where the parent can be null or another key.
        return {
            '__key__': [
                obj.kind(),
                obj.id_or_name(),
                json_encoder(obj.parent())
                ]
            }
    elif isinstance(obj, db.Model):
        # Models are encoded as just their key
        return { '__model__': json_encoder(obj.key()) }

    # There was no special encoding to be done
    return obj

def json_decoder(dct):
    """Decodes objects encoded as one-item dictionaries. See
    json_encoder. NOTE: Models are deserialized as their keys, under the
    assumption that the place(s?) where a model would be serialized (ie,
    ReferenceProperty) accept either a model or its key as a value."""
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
        elif type_name == 'model':
            # For models, we just return their key
            return value
    return dct


def load_fixtures(filename):
    """Loads fixtures from the given path into the datastore."""
    logging.info("Loading fixtures from %s..." % os.path.basename(filename))

    with open(filename, 'r') as f:
        json_obj = json.load(f, object_hook=json_decoder)

    for count, data in enumerate(json_obj):
        model = get_model(data['model'])
        create_entity(model, data.get('key'), data['fields'])

    logging.info("Loaded %d fixtures..." % (count + 1))

def get_model(modelspec):
    """Gets the model class specified in the given modelspec, which should
    be in the format `path.to.models.module.ModelName`."""
    # Split the modelspec into module path and model name
    module_name, model = modelspec.rsplit('.', 1)
    # Import the module
    __import__(module_name, {}, {})
    # Get a reference to the actual module object
    module = sys.modules[module_name]
    # Return the model class from the module
    return getattr(module, model)

def create_entity(model, key, fields):
    """Creates an entity of the given type in the datastore, based on the
    given fields.  ReferenceProperties and ListProperties are containing Keys
    are looked up in the datastore."""

    logging.debug('Creating %s entity with key %r' % (model.kind(), key))

    # The final keyword arguments we'll pass to the entity's constructor
    args = { 'key': key }

    # Gather up the field names and values into the args dict.  The names must
    # be cast to strings to be usable as keyword arguments.
    for field, value in fields.iteritems():
        # Any special casing based on property type should happen here
        prop = getattr(model, field)
        args[str(field)] = value

    # Create and store the entity
    return model(**args).put()

def serialize_entities(modelspec):
    """Serializes all of the entities of the kind specified by the given
    modelspec as JSON."""
    model = get_model(modelspec)
    fields = model.properties()
    entities = [
        { 'model': modelspec,
          'key': entity.key(),
          'fields': dict((name, getattr(entity, name)) for name in fields) }
        for entity in model.all()]
    return json.dumps(entities, default=json_encoder, indent=4)
