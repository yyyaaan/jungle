
# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions


from .models import *
from .serializers import *

class VmViewSet(viewsets.ModelViewSet):
    """API endpoint for VmRegistry"""
    queryset = VmRegistry.objects.all().order_by("vmid")
    serializer_class = VmSerializer
    permission_classes = [permissions.IsAuthenticated]


class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail, no auth required"""
    queryset = VmTrail.objects.all().order_by("vmid")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]