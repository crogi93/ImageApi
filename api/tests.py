import json
import os
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import include, path, reverse
from django.utils import timezone
from django.utils.timezone import timedelta
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase

from .models import CustomUser, Thumbnail, Tier


class TierTest(APITestCase):

    fixtures = ['tiers.yaml']

    def test_basic_tier_values(self):
        self.tier = Tier.objects.get(name='Basic')
        
        self.assertEqual(self.tier.sizes, [200])
        self.assertEqual(self.tier.store_original, False)
        self.assertEqual(self.tier.can_set_expire, False)
        
    def test_premium_tier_values(self):
        self.tier = Tier.objects.get(name='Premium')
        
        self.assertEqual(self.tier.sizes, [200, 400])
        self.assertEqual(self.tier.store_original, True)
        self.assertEqual(self.tier.can_set_expire, False)
        
    def test_enterprise_tier_values(self):
        self.tier = Tier.objects.get(name='Enterprise')
        
        self.assertEqual(self.tier.sizes, [200, 400])
        self.assertEqual(self.tier.store_original, True)
        self.assertEqual(self.tier.can_set_expire, True) 
        
    def test_create_new_tier(self):
        self.tier = Tier()
        self.tier.name = 'new_tier'
        self.tier.sizes = [200, 300]
        self.tier.store_original = True
        self.tier.can_set_expire = True
        self.tier.save()
        
        self.assertEqual(Tier.objects.get(name='new_tier').sizes, [200, 300])               
      
class ThumbnailModelTests(APITestCase):
    fixtures = ['tiers.yaml']
    
    def setUp(self):
        self.user = CustomUser.objects.create(username='test', password='test', tier_id=1)
        settings.MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'media', 'test')
        
    def test_create_thumbnail(self):
        self.thumbnail = Thumbnail()
        self.thumbnail.path = SimpleUploadedFile(name='test.png', content=open('api/fixtures/test.png', 'rb').read(), content_type='image/png')
        self.thumbnail.size = 200
        self.thumbnail.user = self.user
        self.thumbnail.save()
        
        self.assertEqual(len(Thumbnail.objects.all()), 1)     
        
    def test_size_null_verification(self):
        self.thumbnail_test = Thumbnail()
        self.thumbnail_test.path = SimpleUploadedFile(name='test.png', content=open('api/fixtures/test.png', 'rb').read(), content_type='image/png')
        self.thumbnail_test.user = self.user
        self.thumbnail_test.save()
        self.im = Image.open(self.thumbnail_test.path)
        
        self.assertEqual(self.im.height, 565)      
        
class ThumbnailViewSetTests(APITestCase, URLPatternsTestCase):
    fixtures = ['tiers.yaml']
    urlpatterns = [
        path('api/', include('api.urls')),
        ]
    
    def setUp(self):
        self.user = CustomUser.objects.create(username='test', password='test', tier_id=1)
        self.user_2 = CustomUser.objects.create(username='test2', password='test2', tier_id=3)
        self.thumbnail = Thumbnail()
        self.thumbnail.path = SimpleUploadedFile(name='test.png', content=open('api/fixtures/test.png', 'rb').read(), content_type='image/png')
        self.thumbnail.size = 200
        self.thumbnail.user = self.user
        self.thumbnail.save()
            
    def test_get_request_unauthorized(self):
        url = reverse('thumbnails')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_request_authorized(self):
        url = reverse('thumbnails')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         [{
                            'path': self.thumbnail.path.url,
                            'size': self.thumbnail.size
                         }])
        
    def test_post_request_unauthorized(self):
        url = reverse('thumbnails')
        file = Image.new('RGB', (100, 100))

        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.save(tmp_file)
        tmp_file.seek(0)
        response = self.client.post(url, {'file': tmp_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_post_request_wihtout_expire(self):
        url = reverse('thumbnails')
        file = Image.new('RGB', (100, 100))

        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.save(tmp_file)
        tmp_file.seek(0)
        
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'file': tmp_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Thumbnail.objects.filter(user=self.user_2)), 3)
        
    def test_post_request_with_valid_expire(self):
        url = reverse('thumbnails')
        file = Image.new('RGB', (100, 100))

        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.save(tmp_file)
        tmp_file.seek(0)
        
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'file': tmp_file, 'expire_after': 400}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Thumbnail.objects.filter(user=self.user_2)), 3)         
        
    def test_post_request_with_invalid_expire(self):
        url = reverse('thumbnails')
        file = Image.new('RGB', (100, 100))

        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        file.save(tmp_file)
        tmp_file.seek(0)
        
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'file': tmp_file, 'expire_after': 200}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)           
    
    def test_not_expire_at_attribute(self):
        
        self.thumbnail_new = Thumbnail()
        self.thumbnail_new.path = SimpleUploadedFile(name='test.png', content=open('api/fixtures/test.png', 'rb').read(), content_type='image/png')
        self.thumbnail_new.size = 200
        self.thumbnail_new.user = self.user_2
        self.thumbnail_new.expire_at = timezone.now() + timedelta(seconds=300)
        self.thumbnail_new.save()
            
        url = reverse('thumbnails')
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         [{
                            'path': self.thumbnail_new.path.url,
                            'size': self.thumbnail_new.size
                         }])
    
    def test_expire_at_attribute(self):
        
        self.thumbnail_new = Thumbnail()
        self.thumbnail_new.path = SimpleUploadedFile(name='test.png', content=open('api/fixtures/test.png', 'rb').read(), content_type='image/png')
        self.thumbnail_new.size = 200
        self.thumbnail_new.user = self.user_2
        self.thumbnail_new.expire_at = timezone.now() - timedelta(seconds=300)
        self.thumbnail_new.save()
            
        url = reverse('thumbnails')
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [])
