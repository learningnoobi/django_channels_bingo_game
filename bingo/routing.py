from .consumers import BingoConsumer, OnlineRoomConsumer
from django.urls import path

websocket_urlpatterns=[
    path('ws/clicked/<room_name>/',BingoConsumer.as_asgi(),name="clicked"),
    path('ws/online-rooms/',OnlineRoomConsumer.as_asgi())

]