from django.test import TestCase
from django.core.urlresolvers import reverse
from aol.lakes.models import NHDLake as Lake, Photo
from ..forms import LakeForm, PhotoForm

class LakeFormTest(TestCase):
    fixtures = ['lakes.json']

    def test_form(self):
        lake = Lake.objects.get(title="Matt Lake")
        data = {
            "title": lake.title,
            "body": lake.body,
            "gnis_id": lake.gnis_id,
            "gnis_name": lake.gnis_name,
            "reachcode": lake.reachcode,
            "fishing_zone": lake.fishing_zone.pk,
            "huc6": lake.huc6.pk,
            # set some new counties via their pk
            "county_set": [2, 3]
        }

        form = LakeForm(data, instance=lake)
        self.assertTrue(form.is_valid())
        form.save()
        # make sure the counties got changed in the save method
        self.assertEqual(set(c.pk for c in lake.county_set.all()), set(data['county_set']))

    def test_deletable_model_form(self):
        # this tests the DeletableModelForm by testing PhotoForm (which subclasses it)
        lake = Lake.objects.get(title="Matt Lake")
        photo = Photo.objects.filter(lake=lake)[0]

        # make sure the object gets saved
        data = PhotoForm(instance=photo).initial
        data['caption'] = "whatever"
        form = PhotoForm(data, instance=photo)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(data['caption'], Photo.objects.get(pk=photo.pk).caption)

        # make sure the object gets deleted if the do_delete field is marked
        data['do_delete'] = "true"
        form = PhotoForm(data, instance=photo)
        # the form should be valid
        self.assertTrue(form.is_valid())
        form.save()
        # the object should be deleted
        self.assertEqual(Photo.objects.filter(pk=photo.pk).count(), 0)

        # now make sure the do_delete field is missing when no instance is
        # provided to the form
        form = PhotoForm()
        self.assertFalse("do_delete" in form.fields)


