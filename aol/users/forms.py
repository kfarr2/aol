import datetime
from django import forms
from django.db.models import Max
from django.db import transaction
from django.utils.translation import ugettext as _
from django.contrib.flatpages.forms import FlatpageForm as FPF
from aol.utils.forms import DeletableModelForm
from aol.lakes.models import NHDLake, LakeCounty, Plant, LakePlant

class LakeForm(forms.ModelForm):
    class Meta:
        model = NHDLake
        fields = (
            'title',
            'gnis_id',
            'gnis_name',
            'body',
            'parent',
            'aol_page',
        )
        widgets = {
            "body": forms.widgets.Textarea(attrs={"class": "ckeditor"}),
            "parent": forms.widgets.TextInput,
        }

class FlatPageForm(FPF, DeletableModelForm):
    class Meta(FPF.Meta):
        widgets = {
            "content": forms.widgets.Textarea(attrs={"class": "ckeditor"}),
        }

        fields = (
            "url",
            "title",
            "content",
            "template_name",
            "sites",
        )

