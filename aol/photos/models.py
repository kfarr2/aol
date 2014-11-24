import os
from django.conf import settings as SETTINGS
from django.contrib.gis.db import models
from aol.lakes.models import NHDLake
from PIL import Image

# this can't be a lambda because of Django migrations
def upload_to(instance, filename):
    return instance.PHOTO_DIR + filename

class Photo(models.Model):
    """Stores all the photos attached to a lake"""
    PHOTO_DIR = "photos/"
    THUMBNAIL_PREFIX = "thumbnail-"

    photo_id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to=upload_to, db_column="filename")
    taken_on = models.DateField(null=True, db_column="photo_date", blank=True)
    author = models.CharField(max_length=255, blank=True)
    caption = models.CharField(max_length=255, blank=True)

    lake = models.ForeignKey(NHDLake, db_column="reachcode")

    class Meta:
        db_table = "photo"

    def exists(self):
        """Returns True if the file exists on the filesystem"""
        try:
            open(self.file.path)
        except IOError:
            return False
        return True

    @property
    def url(self):
        """Returns the complete path to the photo from MEDIA_URL"""
        return self.file.url

    @property
    def thumbnail_url(self):
        """Returns the complete path to the photo's thumbnail from MEDIA_URL"""
        return SETTINGS.MEDIA_URL + os.path.relpath(self._thumbnail_path, SETTINGS.MEDIA_ROOT)

    @property
    def _thumbnail_path(self):
        """Returns the abspath to the thumbnail file, and generates it if needed"""
        filename = self.THUMBNAIL_PREFIX + os.path.basename(self.file.name)
        path = os.path.join(os.path.dirname(self.file.path), filename)
        try:
            open(path).close()
        except IOError:
            self._generate_thumbnail(path)

        return path

    def _generate_thumbnail(self, save_to_location):
        """Generates a thumbnail and saves to to the save_to_location"""
        SIZE = (400, 300)
        im = Image.open(self.file.path)
        im.thumbnail(SIZE, Image.ANTIALIAS)
        im.save(save_to_location)


