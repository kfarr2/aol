import os
from unittest.mock import Mock
from model_mommy.mommy import make
from model_mommy.generators import gen_image_field
from django.test import TestCase
from django.conf import settings as SETTINGS
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from .models import Photo
from aol.lakes.models import NHDLake as Lake
from aol.users.tests.test_views import LoginMixin

class ModelTest(TestCase):
    def test_url(self):
        # make sure the URL path is valid
        photo = make(Photo, pk=1, file=gen_image_field())
        self.assertEqual(photo.url, "/media/photos/%s" % os.path.basename(photo.file.name))

    def test_thumbnail_url(self):
        photo = make(Photo, pk=1, file=gen_image_field())

        # delete the thumbnail file
        thumb_path = SETTINGS.ROOT('media', 'photos', 'thumbnail-%s' % os.path.basename(photo.file.name))
        thumb_url = "/media/photos/thumbnail-%s" % os.path.basename(photo.file.name)
        try:
            os.remove(thumb_path)
        except OSError:
            pass

        # this should generate a thumbnail
        self.assertEqual(photo.thumbnail_url, thumb_url)
        # make sure the thumbnail file actually exists
        self.assertTrue(os.path.exists(thumb_path))

        # now we want to make sure subsequent calls to the thumbnail_url do not
        # recreate the image (since that would be expensive)

        # overwrite the file
        flag_text = "this should not be overwritten!"
        with open(thumb_path, 'w') as f:
            f.write(flag_text)
        # try getting the thumbnail URL again
        self.assertEqual(photo.thumbnail_url, thumb_url)
        # make sure it didn't recreate the thumbnail
        with open(thumb_path) as f:
            self.assertEqual(f.read(), flag_text)

        # delete the thumbnail file
        try:
            os.remove(thumb_path)
        except OSError:
            pass

class ViewTest(LoginMixin):
    def test_add_photo(self):
        make(Lake, title="Matt Lake", ftype=390, is_in_oregon=True)
        lake = Lake.objects.get(title="Matt Lake")
        response = self.client.get(reverse('admin-add-photo', args=(lake.pk,)))
        self.assertEqual(response.status_code, 200)

        # test posting to the form
        data = {
            'caption': 'foo',
            'author': 'bar',
            'file': open(os.path.join(SETTINGS.MEDIA_ROOT, "photos", "test.jpg"), "rb"),
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
        photo = make(Photo, pk=1, taken_on=now())
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

