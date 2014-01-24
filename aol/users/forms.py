import datetime
from django import forms
from django.db.models import Max
from django.db import transaction
from django.utils.translation import ugettext as _
from django.contrib.flatpages.forms import FlatpageForm as FPF
from aol.lakes.models import Document, NHDLake, LakeCounty, Photo, Plant, LakePlant

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
            if len(attributes) < 7:
                raise forms.ValidationError(_('Missing attributes: Line %d should have 7 attributes separated by 6 tabs. \n Make sure you have 6 tabs separated 7 attributes') % line_no)
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
                    observation_date = attributes[5]
                    plant_info['observation_date'] = datetime.datetime.strptime(observation_date, "%m/%d/%Y").date() if observation_date.strip() else None
                    plant_info['is_aquatic_invasive'] = attributes[5]

                    output.append(plant_info)
                # Now it means the reachcode is invalid
                else:
                    pass
                    # I don't think we care now if the reachcode cannot be found
                    #raise forms.ValidationError(_('Invalid reachcode: Reachcode no. %s is invalid in line %d. \n Erase the line or provide a valid reachcode to continue processing.') % (attributes[0], line_no))

        return output

    def save(self):
        with transaction.atomic():
            LakePlant.objects.all().delete()
            Plant.objects.all().delete()
            for line in self.cleaned_data:
                # Get attribute values at each line
                reach_code = line['reachcode']
                name = line['name']
                common_name = line['common_name']
                plant_family = line['plant_family']
                former_name = line['former_name']
                is_aquatic_invasive = line['is_aquatic_invasive']
                observation_date = line['observation_date']

                # print "%s - %s - %s - %s - %s " % (reach_code, name, common_name, plant_family, former_name)
                # If reach_code is not empty, look up the lake using reachcode
                if reach_code:
                    try:
                        lake = NHDLake.objects.get(reachcode=reach_code)
                    except NHDLake.DoesNotExist:
                        continue

                    # If lakes is not empty, then look for exist plant in database
                    # or create new plant information from user input
                    try:
                        plant = Plant.objects.get(name=name)
                    except Plant.DoesNotExist:
                        plant = Plant(name=name, common_name=common_name, former_name=former_name, plant_family=plant_family, is_aquatic_invasive=is_aquatic_invasive)
                        plant.save()

                    # Add this plant to the lake where it should belong to
                    LakePlant(lake=lake, plant=plant, observation_date=observation_date).save()
