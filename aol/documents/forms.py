import datetime
from django import forms
from django.db.models import Max
from aol.utils.forms import DeletableModelForm
from .models import Document

class DocumentForm(DeletableModelForm):
    class Meta:
        model = Document
        fields = (
            'name',
            'file',
            'rank',
            'type',
            'friendly_filename',
        )

    def __init__(self, *args, **kwargs):
        # initialize the rank with the highest rank + 1
        if kwargs['instance'].pk is None:
            kwargs['instance'].rank = (Document.objects.filter(lake=kwargs['instance'].lake).aggregate(Max('rank'))['rank__max'] or 0) + 1

        super(DocumentForm, self).__init__(*args, **kwargs)


