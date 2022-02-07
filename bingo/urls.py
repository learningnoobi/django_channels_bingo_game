

from django.urls import path
from .views import (
                    bingoView,
                    CreateRoomView,
                    roomExist
                    )
urlpatterns = [
    path('', CreateRoomView , name="create_room"),
    path('<str:room_name>/', bingoView , name="bingo"),
    path('room/check_room/<room_name>/', roomExist , name="check_room"),
    
]
