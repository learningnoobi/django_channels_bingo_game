from django.db import models

# Create your models here.


# this table will only exists when there are people in room
# once all the users are gone this will be deleted
class BingoRoom(models.Model):
    room_name = models.CharField(max_length=50)
    # Live WebSocket connections in this room; the room is deleted when the last one leaves.
    connections = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.room_name


class TrackPlayers(models.Model):
    username = models.CharField(max_length=50)
    room = models.ForeignKey(BingoRoom, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.username
