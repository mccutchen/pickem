import datetime
from ext import jinja2

import settings

environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(settings.TEMPLATE_DIR),
    autoescape=True)

def render_to_string(filename, context={}):
    template = environment.get_or_select_template(filename)
    return template.render(context)


##############################################################################
# Filters, available to all templates
##############################################################################
def dateformat(d, format):
    return getattr(d, 'strftime', lambda x: x)(format)

def key(obj):
    try:
        return obj.key()
    except AttributeError:
        return obj

def _id(obj):
    try:
        return key(obj).id()
    except AttributeError:
        return obj

def keyname(obj):
    try:
        return key(obj).name()
    except AttributeError:
        return obj

environment.filters['dateformat'] = dateformat
environment.filters['key'] = key
environment.filters['id'] = _id
environment.filters['keyname'] = keyname


##############################################################################
# Helper functions, available to all templates
##############################################################################
def url(*args, **kwargs):
    from main import app
    return app.url_for(*args, **kwargs)

environment.globals['url'] = url
