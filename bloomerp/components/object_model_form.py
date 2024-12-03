from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from bloomerp.forms.core import BloomerpModelForm
from bloomerp.models import User
from django.contrib.auth.decorators import login_required

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
    field_name = request.GET.get('field_name', None)

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

    if field_name:
        fields = [field_name]
        Form = modelform_factory(model, fields=fields, form=BloomerpModelForm)
    else:
        Form = modelform_factory(model, fields='__all__', form=BloomerpModelForm)

    if request.method == 'POST':
        form = Form(data=request.POST, files=request.FILES, prefix=form_prefix, model=model)
        if form.is_valid():
            form.save()
            created = True
            new_object = form.instance
    else:
        if object_id:
            instance = model.objects.get(id=object_id)
            form = Form(instance=instance, prefix=form_prefix, model=model, user=user)
        else:
            form = Form(prefix=form_prefix, model=model, user=user)

    return render(request, 'components/object_model_form.html', {'form': form, 'created': created, 'form_prefix': form_prefix, 'new_object': new_object})