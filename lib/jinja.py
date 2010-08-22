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
environment.globals['reverse_url'] = lambda *args: '/XXX'
