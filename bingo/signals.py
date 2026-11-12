from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import BingoRoom

ONLINE_GROUP = "online_bingo_room"


def _broadcast(event_type, command, instance):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        ONLINE_GROUP,
        {
            "type": event_type,
            "command": command,
            "room_name": instance.room_name,
            "room_id": instance.id,
        },
    )


@receiver(post_save, sender=BingoRoom)
def create_room_signal(sender, instance, created, **kwargs):
    if created:
        _broadcast("websocket_room_added", "room_added", instance)


@receiver(post_delete, sender=BingoRoom)
def delete_room_signal(sender, instance, **kwargs):
    _broadcast("websocket_room_deleted", "room_deleted", instance)
