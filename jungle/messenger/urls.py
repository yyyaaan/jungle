from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('', views.SendMsgViewSet)

# api login page disabled, use admin page
app_name = "messenger"
urlpatterns = [
    path('LINE/', views.SendLine.as_view(), name="send-line-shortcut"),
    path('', include(router.urls)),
#    path('auth/', include('rest_framework.urls', namespace='rest_framework'))
]