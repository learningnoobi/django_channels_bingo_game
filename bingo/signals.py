from django.dispatch import receiver    
from django.db.models.signals import post_save,post_delete
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import BingoRoom

channel_layer = get_channel_layer()



@receiver(post_save,sender=BingoRoom)
def create_room_signal(sender, instance, created, *args, **kwargs):
    ins_roomm_name = instance.room_name
    ins_id = instance.id 

    if created:
        async_to_sync(channel_layer.group_send)(
        f'online_bingo_room',
            {
                "type":"websocket_room_added",
                "command":"room_added",
                "room_name":ins_roomm_name,
                "room_id":ins_id
            }
        )


@receiver(post_delete,sender=BingoRoom)
def delete_room_signal(sender, instance, *args, **kwargs):
    print(instance.room_name ,'was deleted')
    ins_roomm_name = instance.room_name
    ins_id = instance.id 
    async_to_sync(channel_layer.group_send)(
    f'online_bingo_room',
        {
            "type":"websocket_room_deleted",
            "command":"room_deleted",
            "room_name":ins_roomm_name,
            "room_id":ins_id
        }
    )