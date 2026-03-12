from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from places.views import PlaceViewSet, CategoryViewSet, TagViewSet, SearchViewSet
from reviews.views import ReviewViewSet

router = DefaultRouter()
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
