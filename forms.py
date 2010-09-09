import logging

from google.appengine.ext.db import djangoforms
from django import forms

import models


class PoolForm(djangoforms.ModelForm):

    class Meta:
        model = models.Pool
        exclude = ('manager',)


class InviteForm(forms.Form):

    emails = forms.CharField(widget=forms.Textarea)

    def clean_emails(self):
        raw_emails = self.cleaned_data['emails']
        emails = [x.split(',') for x in raw_emails.split('\n')]
        emails = [x for y in emails for x in y]
        emails = [x.strip() for x in emails if x.strip()]
        return emails
