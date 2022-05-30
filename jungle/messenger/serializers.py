from rest_framework.serializers import ModelSerializer
from linebot import LineBotApi
from linebot.models import TextSendMessage, FlexSendMessage
from json import loads

from .models import *
from jungle.authentication import get_secret

class MessengerSerializer(ModelSerializer):

    class Meta:
        model = MessengerData
        fields = '__all__'


    def create(self, request):
        validated_request = request

        if "provider" not in request or request["provider"] == "":
            validated_request["provider"] = "LINE"
        if "richcontent" not in request:
            validated_request["richcontent"] = ""

        try:
            if validated_request["provider"] == "LINE":
                KEYS = get_secret("my-messenger", as_json = True)
                linekey = KEYS["LINE-YYY"] if request["audience"] == "YYY" else KEYS["LINE-MSG"]
                client = LineBotApi(linekey)
                res = ""
                if validated_request["richcontent"] == "":
                    res = client.broadcast(TextSendMessage(
                        text=str(request["text"])
                    ))
                else:
                    res = client.broadcast(FlexSendMessage(
                        alt_text = str(request["text"]),
                        contents = loads(request["richcontent"]),
                    ))
                validated_request["response"] = f"OK (Response ID: {res.request_id})"
            else:
                validated_request["response"] = "ERR: no such provider"
        except Exception as ex:
            print(ex)
            validated_request["response"] = f"ERR runtime error due to {str(ex)}"

        return super().create(validated_request) 
