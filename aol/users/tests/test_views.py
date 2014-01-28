import os
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings as SETTINGS
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from aol.lakes.models import NHDLake as Lake, Photo, Document
from ..models import User

class AdminTest(TestCase):
    fixtures = ['lakes.json']
    def setUp(self):
        u = User(username="mdj2", email="mdj2@pdx.edu", first_name="M", last_name="J", is_staff=True)
        u.set_password("password")
        u.save()
        self.client.login(username=u.username, password="password")
        self.site = Site(domain="http://google.com", name="foo")
        self.site.save()

    # just make sure the views return a 200
    def test_listing(self):
        response = self.client.get(reverse('admin-listing'))
        self.assertEqual(response.status_code, 200)

        # test a search
        response = self.client.get(reverse('admin-listing')+"?q=matt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Matt", response.content)

    def test_add_and_edit_flatpage(self):
        # try adding a page
        response = self.client.get(reverse("admin-add-flatpage"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("admin-add-flatpage"), {
            "url": "/foo/",
            "title": "foo",
            "content": "asdf",
            "sites": self.site.pk,
        })
        self.assertRedirects(response, reverse("admin-listing"))

        # now edit the page
        page = FlatPage.objects.first()
        response = self.client.get(reverse("admin-edit-flatpage", args=(page.pk,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("admin-edit-flatpage", args=(page.pk,)), {
            "url": "/foo/",
            "title": "foo",
            "content": "asdf",
            "sites": self.site.pk,
        })
        self.assertRedirects(response, reverse("admin-listing"))




    def test_edit_lake(self):
        lake = Lake.objects.get(title="Matt Lake")
        response = self.client.get(reverse('admin-edit-lake', args=(lake.pk,)))
        self.assertEqual(response.status_code, 200)

        # grab the initial data (which should be valid, and post it back to the form)
        data = response.context['form'].initial
        response = self.client.post(reverse('admin-edit-lake', args=(lake.pk,)), data)
        # the form should be valid, so it should do a redirect
        self.assertEqual(response.status_code, 302)

        # delete a field, thus making the form invalid
        del data['title']
        response = self.client.post(reverse('admin-edit-lake', args=(lake.pk,)), data)
        self.assertFalse(response.context['form'].is_valid())

    def test_add_photo(self):
        lake = Lake.objects.get(title="Matt Lake")
        response = self.client.get(reverse('admin-add-photo', args=(lake.pk,)))
        self.assertEqual(response.status_code, 200)

        # test posting to the form
        data = {
            'caption': 'foo',
            'author': 'bar',
            'file': open(os.path.join(SETTINGS.MEDIA_ROOT, "photos", "test.jpg")),
            'taken_on': '2012-12-12',
        }
        pre_count = Photo.objects.filter(lake=lake).count()
        response = self.client.post(reverse('admin-add-photo', args=(lake.pk,)), data)
        # the response should be valid, so a redirect should happen
        self.assertEqual(response.status_code, 302)
        # make sure the photo got added to the lake
        self.assertEqual(Photo.objects.filter(lake=lake).count(), pre_count + 1)

        # delete a required field to make the form invalid
        del data['caption']
        response = self.client.post(reverse('admin-add-photo', args=(lake.pk,)), data)
        self.assertFalse(response.context['form'].is_valid())

    def test_edit_photo(self):
        photo = Photo.objects.get(pk=1)
        response = self.client.get(reverse('admin-edit-photo', args=(photo.pk,)))
        self.assertEqual(response.status_code, 200)

        # edit the photo
        data = response.context['form'].initial
        data['caption'] = "whatever"
        response = self.client.post(reverse('admin-edit-photo', args=(photo.pk,)), data)
        # the response should be valid, so a redirect should happen
        self.assertEqual(response.status_code, 302)

        # make sure the caption got updated
        photo = Photo.objects.get(pk=1)
        self.assertEqual(photo.caption, data['caption'])

    def test_add_document(self):
        lake = Lake.objects.get(title="Matt Lake")
        response = self.client.get(reverse('admin-add-document', args=(lake.pk,)))
        self.assertEqual(response.status_code, 200)

        # test posting to the form
        data = {
            'name': 'foo',
            'rank': '1',
            'file': open(os.path.join(SETTINGS.MEDIA_ROOT, "photos", "test.jpg")),
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

