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

environment.filters['dateformat'] = dateformat


##############################################################################
# Helper functions, available to all templates
##############################################################################
def url(*args, **kwargs):
    from main import app
    return app.url_for(*args, **kwargs)

environment.globals['url'] = url
