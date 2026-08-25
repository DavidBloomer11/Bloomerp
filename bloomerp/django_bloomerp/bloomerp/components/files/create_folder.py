from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from bloomerp.router import router
from bloomerp.utils.requests import render_blank_form, render_page_refresh
from django.forms import Form
from django import forms

class CreateFolderForm(Form):
    name = forms.CharField(
        max_length=255
    )



@router.register(
    path="components/files/create_folder",
    url_name="components_create_folder"
)
@login_required
def create_folder(request: HttpRequest) -> HttpResponse:
    """Endpoint to create a folder

    Args:
        request (HttpRequest): the request object

    Returns:
        HttpResponse: the response
    """
    
    form = CreateFolderForm(
        data=request.POST if request.method == "POST" else None
    )
    
    if request.method == "POST":
        
        return render_page_refresh()    
    
    
    return render_blank_form(
        request,
        form,
        reverse("components_create_folder")
    )

    
    
