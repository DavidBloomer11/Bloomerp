from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from bloomerp.forms.core import BloomerpModelForm
from bloomerp.models import User
from django.contrib.auth.decorators import login_required
from django import forms

@login_required
@route('object_model_form')
def object_model_form(request:HttpRequest) -> HttpResponse:
    '''
    Component to create an object of a model.
    Requires content_type_id and form_prefix in the query parameters.
    '''
    # Get the content type id and form prefix from the query parameters
    content_type_id = request.GET.get('content_type_id')
    form_prefix = request.GET.get('form_prefix','')
    object_id = request.GET.get('object_id', None)
    fields = request.GET.getlist('field_name', None)
    fields_hidden = request.GET.getlist('field_name_hidden', None)
    reset_on_submit = request.GET.get('reset_on_submit', False)

    # Add permission check here
    user : User = request.user

    # Attributes to be passed to the template
    created = False
    new_object = None


    if not content_type_id:
        return HttpResponse('content_type_id required in the query parameters', status=400)
    
    # Get the model and create a form
    model = ContentType.objects.get(id=content_type_id).model_class()

    # Permission check
    if not user.has_perm(f'{model._meta.app_label}.add_{model._meta.model_name}') and not user.has_perm(f'{model._meta.app_label}.change_{model._meta.model_name}'):
        return HttpResponse('User does not have permission to add objects of this model')

    # Create the form
    if fields:
        Form : BloomerpModelForm = modelform_factory(model, fields=fields, form=BloomerpModelForm)
    else:
        Form : BloomerpModelForm = modelform_factory(model, fields='__all__', form=BloomerpModelForm)

    if request.method == 'POST':
        form : BloomerpModelForm = Form(data=request.POST, files=request.FILES, prefix=form_prefix, model=model)
        if form.is_valid():
            form.save()
            created = True
            new_object = form.instance
        if reset_on_submit:
            form = Form(prefix=form_prefix, model=model, user=user)
    else:
        if fields_hidden:
            Form = hide_fields(Form, fields_hidden)
        
        if object_id:
            instance = model.objects.get(id=object_id)
            form = Form(instance=instance, prefix=form_prefix, model=model, user=user)
        else:
            form = Form(prefix=form_prefix, model=model, user=user)

    return render(request, 'components/object_model_form.html', {'form': form, 'created': created, 'form_prefix': form_prefix, 'new_object': new_object, 'reset_on_submit': reset_on_submit})


def hide_fields(Form, fields) -> BloomerpModelForm:
    '''
    Hides the fields in the form
    '''
    for field in fields:
        try:
            Form.base_fields[field].widget = forms.HiddenInput()
        except KeyError:
            pass
    return Form

