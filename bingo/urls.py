

from django.urls import path
from .views import bingoView,CreateRoomView
urlpatterns = [

    path('', CreateRoomView , name="bingo"),
    path('<str:room_name>/', bingoView , name="bingo"),
]
