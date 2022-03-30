from google.cloud import secretmanager
from logging import getLogger

logger = getLogger("commonlib")
GSM_CLIENT = secretmanager.SecretManagerServiceClient()

def get_secret(keyname):
    name = f"projects/yyyaaannn/secrets/{keyname}/versions/latest"
    response = GSM_CLIENT.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
