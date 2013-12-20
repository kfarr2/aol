from django import forms
from aol.lakes.models import Document, Lake, LakeCounty, Photo, Plant

class LakeForm(forms.ModelForm):
    def save(self, *args, **kwargs):
        """
        We need to override the save method because of the LakeCounty m2m
        table
        """
        kwargs['commit'] = False
        super(LakeForm, self).save(*args, **kwargs)
        self.instance.save()
        # save the m2m
        # delete all existing counties
        LakeCounty.objects.filter(lake=self.instance).delete()
        # add all the counties from the form
        for county in self.cleaned_data['county_set']:
            LakeCounty(lake=self.instance, county=county).save()

    class Meta:
        model = Lake
        fields = (
            'title',
            'body',
            'gnis_id',
            'gnis_name',
            'reachcode',
            'fishing_zone',
            'huc6',
            'county_set',
        )

class DeletableModelForm(forms.ModelForm):
    """
    This form adds a do_delete field which is checked when the modelform is
    saved. If it is true, the model instance is deleted
    """
    do_delete = forms.BooleanField(required=False, initial=False, label="Delete")

    def __init__(self, *args, **kwargs):
        super(DeletableModelForm, self).__init__(*args, **kwargs)
        # if we are adding a new model (the instance.pk will be None), then
        # there is no reason to have a delete option, since the object hasn't
        # been created yet
        if self.instance.pk is None:
            self.fields.pop("do_delete")

    def save(self, *args, **kwargs):
        if self.cleaned_data.get('do_delete'):
            self.instance.delete()
        else:
            super(DeletableModelForm, self).save(*args, **kwargs)


class DocumentForm(DeletableModelForm):
    class Meta:
        model = Document
        fields = (
            'name',
            'file',
            'rank',
        )


class PhotoForm(DeletableModelForm):
    class Meta:
        model = Photo
        fields = (
            'caption',
            'author',
            'file',
            'taken_on',
        )

class PlantForm(forms.Form):
    user_input = forms.CharField(widget=forms.Textarea)


