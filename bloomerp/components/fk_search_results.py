from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.contenttypes.models import ContentType
from bloomerp.models import BloomerpModel
from bloomerp.utils.models import string_search
from django.contrib.auth.decorators import login_required

@login_required
@route('fk_search_results')
def fk_search_results(request:HttpRequest) -> HttpResponse:
    Model : BloomerpModel = ContentType.objects.get_for_id(request.GET.get('content_type_id')).model_class()
    query = request.GET.get('foreign_field_query')
    field_name = request.GET.get('field_name')
    search_type = request.GET.get('search_type','fk')
    if query:
        # Check if the model has a string_search method
        if not hasattr(Model, 'string_search'):
            # Perform a simple search if the method is not found
            Model.string_search = classmethod(string_search)
        
        context = {
            'objects': Model.string_search(query)
        }
    else:
        context = {
            'objects': Model.objects.none()
        }

    context['field_name'] = field_name
    context['type'] = search_type

    return render(request, 'components/fk_search_results.html', context)