from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager 

class User(AbstractBaseUser):
    """A custom user model. Not really necessary yet"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, db_index=True)
    email = models.EmailField(max_length=100)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, blank=True)
    is_staff = models.BooleanField(default=False, blank=True)

    USERNAME_FIELD = 'username'

    objects = UserManager()

    class Meta:
        db_table = "user"

    #
    # These methods are required to work with Django's admin
    #
    def get_full_name(self): return self.first_name + " " + self.last_name
    def get_short_name(self): return self.first_name + " " + self.last_name

    # we don't need granular permissions; all staff will have access to
    # everything
    def has_perm(self, perm, obj=None): return True
    def has_module_perms(self, app_label): return True
