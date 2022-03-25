from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'vms', views.VmViewSet)
router.register(r'trails', views.VmTrailViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# api login page disabled, use admin page
app_name = "ycrawl"
urlpatterns = [
    path('', include(router.urls)),
#    path('auth/', include('rest_framework.urls', namespace='rest_framework'))
]