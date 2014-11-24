from model_mommy.mommy import make
from django.test import TestCase
from django.core.urlresolvers import reverse
from aol.lakes.models import NHDLake as Lake
from ..forms import LakeForm
from aol.documents.forms import DocumentForm
from aol.documents.models import Document
from aol.photos.models import Photo
from aol.photos.forms import PhotoForm

class LakeFormTest(TestCase):
    def test_form(self):
        lake = make(Lake, title="Matt Lake", ftype=390, parent=None, is_in_oregon=True)
        lake = Lake.objects.get(title="Matt Lake")
        data = {
            "title": lake.title,
            "body": lake.body,
            "gnis_id": lake.gnis_id,
            "gnis_name": lake.gnis_name,
            "reachcode": lake.reachcode,
        }

        form = LakeForm(data, instance=lake)
        self.assertTrue(form.is_valid())
        form.save()

    def test_deletable_model_form(self):
        lake = make(Lake, title="Matt Lake", ftype=390, parent=None, is_in_oregon=True)
        make(Photo, lake=lake)
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


