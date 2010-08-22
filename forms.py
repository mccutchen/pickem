import logging

from google.appengine.ext.db import djangoforms
from django import forms

import models


class PoolForm(djangoforms.ModelForm):

    class Meta:
        model = models.Pool
        exclude = ('manager',)
