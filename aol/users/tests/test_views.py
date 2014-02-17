import os
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings as SETTINGS
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from aol.lakes.models import NHDLake as Lake
from ..models import User

class LoginMixin(TestCase):
    def setUp(self):
        u = User(username="mdj2", email="mdj2@pdx.edu", first_name="M", last_name="J", is_staff=True)
        u.set_password("password")
        u.save()
        self.client.login(username=u.username, password="password")
        self.site = Site(domain="http://google.com", name="foo")
        self.site.save()


class AdminTest(LoginMixin):
    fixtures = ['lakes.json']

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
        data['parent'] = ""
        response = self.client.post(reverse('admin-edit-lake', args=(lake.pk,)), data)
        # the form should be valid, so it should do a redirect
        self.assertEqual(response.status_code, 302)

        # delete a field, thus making the form invalid
        del data['gnis_name']
        response = self.client.post(reverse('admin-edit-lake', args=(lake.pk,)), data)
        self.assertFalse(response.context['form'].is_valid())

