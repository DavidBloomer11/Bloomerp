from django.http import HttpRequest
from django.shortcuts import render
from bloomerp.router import router
from bloomerp.utils.requests import render_message

@router.register(
    path="components/communication/delete_inbox_item",
    url_name="components_delete_inbox_item"
)
def delete_inbox_item(request:HttpRequest):
    """
    Renders the delete inbox item page for a given user and inbox type.

    Args:
        request (HttpRequest): The HTTP request object containing GET parameters.
    """
    
    return render_message(
        request,
        message="Item deleted successfully.",
        message_type="success",
    )



