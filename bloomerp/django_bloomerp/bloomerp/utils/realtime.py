from typing import Literal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from pydantic import BaseModel
from enum import Enum

class RealtimeType(Enum):
    TOAST = "toast"
    INBOX_NOTIFICATION = "inbox_notification"


MessageType = Literal["success", "info", "danger", "warning"]

class ToastPayload(BaseModel):
    message_type:MessageType
    message:str
    duration:int=5

class NotificationPayload(BaseModel):
    notification_count:int
    toast_payload:ToastPayload


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
    

def send_toast_message(user_id:int, payload:ToastPayload):
    """Sends a toast message to the user

    Args:
        user_id (int): the user id
        payload (ToastPayload): the payload
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}_inbox',
        {
            'type': 'notify',
            'payload': {
                "type" : RealtimeType.TOAST.value,
                "data" : payload.model_dump()    
            },
        },
    )


def send_user_inbox_message(
    user_id: int, 
    payload:NotificationPayload
    ) -> None:
    """Sends an inbox message

    Args:
        user_id (int): The ID of the user to send the message to.
        payload (dict): The message payload to send.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'notify',
            'payload': {
                "type" : RealtimeType.INBOX_NOTIFICATION.value,
                "data" : payload.model_dump()
                    
            },
        },
    )
