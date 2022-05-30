from rest_framework import authentication
from base64 import decode
from google.cloud import secretmanager
from json import loads


class BearerAuthentication(authentication.TokenAuthentication):
    keyword = 'Bearer'


def get_secret(keyname, as_json=False):
    GSM_CLIENT = secretmanager.SecretManagerServiceClient()
    
    name = f"projects/yyyaaannn/secrets/{keyname}/versions/latest"
    response = GSM_CLIENT.access_secret_version(request={"name": name})
    decoded = response.payload.data.decode("UTF-8")
    
    if as_json:
        return loads(decoded)
    return decoded
