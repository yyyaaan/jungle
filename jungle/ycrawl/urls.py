from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'actions', views.VmActionLogViewSet)
router.register(r'trails', views.VmTrailViewSet)
router.register(r'vms', views.VmViewSet)
router.register(r'configs', views.YCrawlConfigViewSet)

# api login page disabled, use admin page
app_name = "ycrawl"
urlpatterns = [
    path('', include(router.urls)),
    path('START/', views.StartYcrawl.as_view(), name="start_ycrawl"),
    path('GETNODES/', views.GetNodeJobs.as_view(), name="get_nodes_jobs"),
#    path('auth/', include('rest_framework.urls', namespace='rest_framework'))
]