from django import forms
from aol.utils.forms import DeletableModelForm
from .models import Photo

class PhotoForm(DeletableModelForm):
    class Meta:
        model = Photo
        fields = (
            'caption',
            'author',
            'file',
            'taken_on',
        )


