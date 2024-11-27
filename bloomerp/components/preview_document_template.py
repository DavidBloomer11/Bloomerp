from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, FileResponse
from bloomerp.utils.document_templates import DocumentController
from bloomerp.models import DocumentTemplate
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
import json
from django.contrib.auth.decorators import login_required
from bloomerp.utils.object_generator import random_object_factory

@login_required
@xframe_options_exempt
@route('preview_document_template')
def preview_document_template(request:HttpRequest) -> HttpResponse:
    # Some permissions check
    if not request.user.has_perm('bloomerp.view_documenttemplate'):
        return HttpResponse('User does not have permission to view document templates')
    try:
        data : dict = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    
    template_id = data.get('template_id')
    content = data.get('content')

    document_template = get_object_or_404(DocumentTemplate, id=template_id)
    if content:
        document_template.template = content

    try:
        document_controller = DocumentController()

        # Generate a random object for the template
        model = document_template.model_variable.model_class()
        random_object = random_object_factory(model)


        # Create the preview document
        file_bytes = document_controller.create_preview_document(
            template=document_template,
            data={'object': random_object}
        )

        # Return the PDF file as a FileResponse
        response = HttpResponse(file_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="dynamic.pdf"'
        return response
    except Exception as e:
        # Display errors to the user in the template
        # Display entire stack trace in development
        return HttpResponse(str(e), status=200)
