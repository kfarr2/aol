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
            "content": forms.widgets.Textarea(attrs={"class": "ckeditor"})
        }



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
