from os import path

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from PIL import Image

from api.managers import UserManager
from api.validators import JSONSchemaValidator


SIZES_FIELD_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'number'
    }
}

def upload_path(instance, filename):
    size = str(instance.size) if instance.size else 'O'
     
    return '_'.join([str(instance.user.id), size, filename])
    
class Tier(models.Model):
    name = models.CharField(max_length=50)
    sizes = models.JSONField('Sizes', validators=[JSONSchemaValidator(limit_value=SIZES_FIELD_SCHEMA)])
    store_original = models.BooleanField(default=False)
    can_set_expire = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
class CustomUser(AbstractUser):
    tier = models.ForeignKey(Tier, verbose_name='tier', on_delete=models.CASCADE)
        
    objects = UserManager()
    
    REQUIRED_FIELDS = ['email', 'tier']
    
class Thumbnail(models.Model):
    path = models.ImageField(upload_to=upload_path)
    size = models.IntegerField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, related_name='owner', on_delete=models.CASCADE)
    expire_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self) -> str:
        return str(self.path)