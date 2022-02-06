from .consumers import BingoConsumer
from django.urls import path

websocket_urlpatterns=[
    path('ws/clicked/<room_name>/',BingoConsumer.as_asgi(),name="clicked")

]