
# Create your views here.
from rest_framework import viewsets, views, permissions, renderers, status
from rest_framework.response import Response
from django.shortcuts import render
from datetime import date
from json import dumps

from .models import *
from .serializers import *


API_RENDERERS = [renderers.AdminRenderer, renderers.BrowsableAPIRenderer, renderers.JSONRenderer, renderers.JSONOpenAPIRenderer]

class SendMsgViewSet(viewsets.ModelViewSet):
    """Sending action is done in serializer"""

    queryset = MessengerData.objects.all().order_by("-timestamp")
    serializer_class = MessengerSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = API_RENDERERS

class SendLine(views.APIView):
    """A shortcut to send line message"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        validated_request = {"provider": "LINE"}

        if "text" not in request.data:
            return Response({"success": False, "info": "text cannot be empty"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        validated_request["text"] = request.data["text"]
        validated_request["audience"] = request.data["to"] if "to" in request.data else "Cloud"
        validated_request["richcontent"] = dumps(request.data["flex"]) if "flex" in request.data else ""
        
        msg_serializer = MessengerSerializer(data=validated_request)
        if msg_serializer.is_valid(raise_exception=True):
            msg_serializer.save()

        return Response({"sucess": True}, status=status.HTTP_201_CREATED)


