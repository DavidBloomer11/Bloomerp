from rest_framework.views import APIView
from bloomerp.api.base import AUTHENTICATION_CLASSES

class BaseBloomerpApiView(APIView):
    authentication_classes = AUTHENTICATION_CLASSES