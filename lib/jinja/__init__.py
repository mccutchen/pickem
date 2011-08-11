import inspect
import logging

from ext import jinja2

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


# Add our custom filters, helpers and tests
add_module_to_env(filters, environment.filters)
add_module_to_env(helpers, environment.globals)
add_module_to_env(tests, environment.tests)


# Enabling this monkeypatch can help track down hard to find errors that crop
# up during template rendering (since Jinja's own error reporting is so
# unhelpful on AppEngine).
real_handle_exception = environment.handle_exception
def handle_exception(self, *args, **kwargs):
	import logging, traceback
	logging.error('Template exception:\n%s', traceback.format_exc())
	real_handle_exception(self, *args, **kwargs)
environment.handle_exception = handle_exception
