# -*- coding: utf-8 -*-
from django.conf import settings
from django import http
from django.template.context import get_standard_processors

# The Jinja environment
from environment import environment

DEFAULT_MIMETYPE = getattr(settings, 'DEFAULT_CONTENT_TYPE')

# Django-alike shortcuts
def render_to_string(filename, context={}, request=None):
	template = environment.get_or_select_template(filename)
	if request:
		for processor in get_standard_processors():
			context.update(processor(request))
	return template.render(context)

def render_to_response(filename, context={}, mimetype=DEFAULT_MIMETYPE,
                       status=200, request=None):
	return http.HttpResponse(
		render_to_string(filename, context, request),
		status=status,
		mimetype=mimetype)

def direct_to_template(request, template, context={},
                       mimetype=DEFAULT_MIMETYPE, status=200):
	return render_to_response(template, context=context, mimetype=mimetype,
                              status=status, request=request)
