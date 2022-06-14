from django.urls import path, include

from api import views


urlpatterns = [
    path('thumbnails', views.ThumbnailList.as_view(), name='thumbnails'),
]