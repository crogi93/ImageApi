import io
import os

from django.db.models import Q
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Thumbnail
from .serializers import CreateThumbnailSerializer, ThumbnailSerializer


class ThumbnailList(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get(self, request, format=None):
        user = self.request.user
        now = timezone.now()

        thumbnails = Thumbnail.objects.filter(Q(user=user), Q(expire_at__gte=now) | Q(expire_at=None))
        serializer = ThumbnailSerializer(thumbnails, many=True)
        
        return Response(serializer.data)

    def post(self, request, format=None):
        user = request.user
        tier = user.tier
        file = request.FILES.get('file')
        
        sizes = tier.sizes
        expire_after = None
        
        if tier.can_set_expire and self.request.data.get('expire_after'):
            expire_after = int(self.request.data.get('expire_after'))
        
        request_data = []
        entry = {
            'user': user.id,
            'path': file,
            'expire_after': expire_after,
        }
        
        if tier.store_original:
            entry['size'] = None
            request_data.append(entry.copy())  

        for size in sizes:
            im = Image.open(io.BytesIO(file.read()))
            width = int(size / im.height * im.width)
            im = im.resize((width, size))
            
            entry['size'] = size
            output = io.BytesIO()
            im.save(output, format='PNG')
            file.seek(0)
            output.seek(0)
            
            filename = os.path.splitext(file.name)[0] + '.png'
            entry['path'] = SimpleUploadedFile(name=filename, content=output.read(), content_type='image/png')
            request_data.append(entry.copy())

        serializer = CreateThumbnailSerializer(data=request_data, many=True)
        
        if  not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
