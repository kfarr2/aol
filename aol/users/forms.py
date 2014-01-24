from django import forms
from django.db.models import Max
from aol.lakes.models import Document, NHDLake, LakeCounty, Photo, Plant
from django.utils.translation import ugettext as _
from django.contrib.flatpages.forms import FlatpageForm as FPF

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
        model = NHDLake
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
        widgets = {
            "body": forms.widgets.Textarea(attrs={"class": "ckeditor"})
        }

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

class FlatPageForm(FPF, DeletableModelForm):
    class Meta(FPF.Meta):
        widgets = {
            "content": forms.widgets.Textarea(attrs={"class": "ckeditor"})
        }



class DocumentForm(DeletableModelForm):
    class Meta:
        model = Document
        fields = (
            'name',
            'file',
            'rank',
        )

    def __init__(self, *args, **kwargs):
        # initialize the rank with the highest rank + 1
        if kwargs['instance'].pk is None:
            kwargs['instance'].rank = Document.objects.filter(lake=kwargs['instance'].lake).aggregate(Max('rank'))['rank__max'] + 1

        super(DocumentForm, self).__init__(*args, **kwargs)


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

    def clean(self):
        cleaned_data = super(PlantForm, self).clean()
        data = cleaned_data.get("user_input", "").split('\n')

        # Create a list of plant infomation output
        output = []
        line_no = 0
        for line in data:

            # Each plant_info is a dictionary
            plant_info = {}
            line_no = line_no + 1
            attributes = line.split('\t')

            # Check if there are enough attributes
            # Each line should have 5 attributes, which are separated by tab
            if len(attributes) < 5:
                raise forms.ValidationError(_('Missing attributes: Line %d should have 5 attributes separated by 4 tabs. \n Make sure you have 4 tabs separated 5 attributes') % line_no)
            # Check if reachcode is available and should not be the header
            elif attributes[0] and attributes[0] != 'ReachCode':
                lakes = NHDLake.objects.filter(reachcode=attributes[0])

                # Check if that reachcode is corresponding to a lake or a list of lakes
                if lakes:
                    plant_info['reachcode'] = attributes[0]
                    plant_info['name'] = attributes[1]
                    plant_info['common_name'] = attributes[2]
                    plant_info['plant_family'] = attributes[3]
                    plant_info['former_name'] = attributes[4]

                    output.append(plant_info)
                # Now it means the reachcode is invalid
                else:
                    raise forms.ValidationError(_('Invalid reachcode: Reachcode no. %s is invalid in line %d. \n Erase the line or provide a valid reachcode to continue processing.') % (attributes[0], line_no))

                
        return output
