from django.utils import timezone
from django.utils.timezone import timedelta

from rest_framework import serializers

from .models import Thumbnail


MIN_EXPIRE_AFTER = 300
MAX_EXPIRE_AFTER = 30000

class ThumbnailSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = Thumbnail
        fields = ['path', 'size']
        
class CreateThumbnailSerializer(serializers.ModelSerializer):
    expire_after = serializers.IntegerField(min_value=MIN_EXPIRE_AFTER, max_value=MAX_EXPIRE_AFTER, allow_null=True)
    
    class Meta:
        model = Thumbnail
        fields = ['path', 'size', 'user', 'expire_after']
        
    def create(self, validated_data):
        expire_after = validated_data.pop('expire_after')
        if expire_after:
            validated_data['expire_at'] = timezone.now() + timedelta(seconds=expire_after)
        
        return Thumbnail.objects.create(**validated_data)    
        