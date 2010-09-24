import inspect
import logging

from ext import jinja2
from django.template import defaultfilters

import filters, helpers, tests
import settings


# The environment used to render every template
environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(settings.TEMPLATE_DIR),
    undefined=jinja2.Undefined,
    autoescape=True)

# A shortcut for rendering a template with the default environment
def render_to_string(filename, context={}):
    template = environment.get_or_select_template(filename)
    return template.render(context)


##############################################################################
# Utility functions
##############################################################################
def add_module_to_env(module, env_place, exceptions=None):
    """Adds the callable contents of the given module to the given 'place'
    (for lack of a better name) in a Jinja environment.  Useful for, e.g.,
    adding all of the filter functions in a 'filters' module to the filters of
    the given environment."""
    exceptions = exceptions or set()
    for name, value in inspect.getmembers(module, callable):
        if name not in exceptions:
            name = getattr(value, 'jinja_name', name)
            env_place[name] = value


##############################################################################
# Filters, available to all templates
##############################################################################
add_module_to_env(defaultfilters, environment.filters,
                  exceptions=set(('safe', 'default')))
add_module_to_env(filters, environment.filters)


##############################################################################
# Helper functions, available to all templates
##############################################################################
add_module_to_env(helpers, environment.globals)

# Also make some settings available to all templates
environment.globals['PRODUCTION'] = settings.PRODUCTION
environment.globals['DEBUG'] = settings.DEBUG
environment.globals['LOGO'] = jinja2.Markup('Pick&#8217;em Pick&#8217;em')

##############################################################################
# Custom tests
##############################################################################
add_module_to_env(tests, environment.tests)
