from django.apps import apps
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from bloomerp.models import BloomerpModel
from bloomerp.utils.router import route
from bloomerp.models import Link
from bloomerp.utils.models import search_models_by_query

@route('search_results')
def search_results(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('search_results_query', '')  # Retrieve the search query from the GET parameters
    results = []

    links = None

    if query == '':
        return HttpResponse('<li class="dropdown-item">No query provided</li>')

    if query.startswith('/') and query[1] != '/':
        # In this case we want to return links for a specific model
        # Name is optional and comes after a : in the query
        sub_query = query[1:]

        name = None
        if ':' in sub_query:
            sub_query, name = sub_query.split(':')

        content_types = search_models_by_query(sub_query)
        list_level_links = []

        for content_type in content_types:
            links = Link.objects.filter(content_type=content_type, level='LIST')
            if name:
                links = links.filter(name__icontains=name)
            
            list_level_links.append({
                'model_name': content_type.model_class()._meta.verbose_name,
                'links': links
            })
        return render(request, 'components/search_results.html', {'list_level_links': list_level_links})
    
    if query.startswith('//'):
        # In this case, we want to return app level links
        sub_query = query[2:]
        app_level_links = Link.objects.filter(level='APP', name__icontains=sub_query)

        return render(request, 'components/search_results.html', {'app_level_links': app_level_links})

    # Get all models from the app
    all_models = apps.get_models()
    # Iterate over all models
    for model in all_models:
        # Check if user has permission to view the model
        if not request.user.has_perm(f'{model._meta.app_label}.view_{model._meta.model_name}'):
            continue

        # Check if the model inherits from BloomerpModel and allows string search
        if issubclass(model, BloomerpModel) and getattr(model, 'allow_string_search', False):
            # Perform string search using the static method
            matching_objects = model.string_search(query)

            # If there are matching objects, add them to the results
            if matching_objects.exists():
                if len(matching_objects) > 5:
                    matching_objects = matching_objects[0:5]

                results.append({
                    "model_name": model._meta.verbose_name_plural,
                    "objects": matching_objects
                })


    context = {
        "results": results,
        "query": query
    }

    return render(request, 'components/search_results.html', context)
