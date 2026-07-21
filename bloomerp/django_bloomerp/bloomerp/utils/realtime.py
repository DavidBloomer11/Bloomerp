from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from openai import BaseModel


def send_user_message(user_id: int, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'notify',
            'payload': payload,
        },
    )
    

class InboxMessagePayload(BaseModel):
    count: int
    
    


def send_user_inbox_message(user_id: int, payload: dict) -> None:
    """Sends a inbox message

    Args:
        user_id (int): The ID of the user to send the message to.
        payload (dict): The message payload to send.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}_inbox',
        {
            'type': 'notify',
            'payload': payload,
        },
    )
