import os
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings as SETTINGS
from .models import Document
from aol.users.tests.test_views import LoginMixin
from aol.lakes.models import NHDLake as Lake

class ViewTest(LoginMixin):
    fixtures = ['lakes.json']

    def test_add_document(self):
        lake = Lake.objects.get(title="Matt Lake")
        response = self.client.get(reverse('admin-add-document', args=(lake.pk,)))
        self.assertEqual(response.status_code, 200)

        # test posting to the form
        data = {
            'name': 'foo',
            'rank': '1',
            'file': open(os.path.join(SETTINGS.MEDIA_ROOT, "photos", "test.jpg")),
            'type': Document.OTHER,
        }
        pre_count = Document.objects.filter(lake=lake).count()
        response = self.client.post(reverse('admin-add-document', args=(lake.pk,)), data)
        # the response should be valid, so a redirect should happen
        self.assertEqual(response.status_code, 302)
        # make sure the document got added to the lake
        self.assertEqual(Document.objects.filter(lake=lake).count(), pre_count + 1)

        # delete a required field to make the form invalid
        del data['name']
        response = self.client.post(reverse('admin-add-document', args=(lake.pk,)), data)
        self.assertFalse(response.context['form'].is_valid())

    def test_edit_document(self):
        document = Document.objects.get(pk=1)
        response = self.client.get(reverse('admin-edit-document', args=(document.pk,)))
        self.assertEqual(response.status_code, 200)

        # edit the document
        data = response.context['form'].initial
        data['name'] = "whatever"
        response = self.client.post(reverse('admin-edit-document', args=(document.pk,)), data)
        # the response should be valid, so a redirect should happen
        self.assertEqual(response.status_code, 302)

        # make sure the caption got updated
        document = Document.objects.get(pk=1)
        self.assertEqual(document.name, data['name'])

