from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'actions', views.VmActionLogViewSet)
router.register(r'vms', views.VmViewSet)
router.register(r'trails', views.VmTrailViewSet)

# api login page disabled, use admin page
app_name = "ycrawl"
urlpatterns = [
    path('', include(router.urls)),
#    path('auth/', include('rest_framework.urls', namespace='rest_framework'))
]