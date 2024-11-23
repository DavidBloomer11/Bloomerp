from django.views.generic import DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from bloomerp.models import DocumentTemplate, File
from bloomerp.forms.document_templates import FreeVariableForm
from django.shortcuts import redirect
from django.contrib import messages
from bloomerp.utils.document_templates import DocumentController
from django.contrib.contenttypes.models import ContentType
from bloomerp.utils.router import BloomerpRouter
from bloomerp.views.mixins import BloomerpModelContextMixin
from bloomerp.views.core import BloomerpBaseDetailView
from django.views.generic.edit import UpdateView
from bloomerp.utils.models import get_detail_base_view_url

# ---------------------------------
# Bloomerp Detail Document Template List View
# ---------------------------------
router = BloomerpRouter()

@router.bloomerp_route(
    path="document-templates", 
    name="Document Templates List for {model} model",
    url_name="document_templates_list",
    description="List of document templates for the {model} model",
    route_type="detail",
    exclude_models=[DocumentTemplate]
    )
class BloomerpDetailDocumentTemplateListView(PermissionRequiredMixin, BloomerpBaseDetailView):
    settings = None
    template_name = "document_template_views/bloomerp_document_template_list_view.html"
    document_template_detail_url = "document_template_detail_editor" # URL to view document template detail
    document_template_generate_url = "" # URL to generate document template for a specific instance

    def get_permission_required(self):
        return [f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get related document templates
        content_type = ContentType.objects.get_for_model(self.model)

        context["document_templates"] = DocumentTemplate.objects.filter(
            model_variable=content_type
        )
        context["document_template_detail_url"] = self.document_template_detail_url
        context["document_template_generate_url"] = get_detail_base_view_url(self.model) + "_document_template_generate"
        return context

# ---------------------------------
# Bloomerp Detail Document Template Generate View
# ---------------------------------

@router.bloomerp_route(
    path="document-templates/<int:template_id>/", 
    name="Document Template generate for {model}",
    route_type="detail",
    url_name="document_template_generate",
    description="Document Template for {model}",
    exclude_models=[DocumentTemplate]
    )
class BloomerpDetailDocumentTemplateGenerateView(PermissionRequiredMixin, BloomerpBaseDetailView):
    template_name = "document_template_views/bloomerp_detail_document_generator_view.html"
    model = None

    def get_permission_required(self):
        return [f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"]

    def post(self, request, *args, **kwargs):
        # Retrieve the instance based on the provided ID
        template_id = self.kwargs["template_id"]
        # Use the retrieved ID as desired
        template = DocumentTemplate.objects.get(pk=template_id)
        
        try:
            if "instance_select" in request.POST:
                id = request.POST.get("instance_select")
                instance = template.model_variable.get_object_for_this_type(pk=id)
            else:
                instance = self.get_object()

            free_variable_form = FreeVariableForm(template, request.POST)

            if free_variable_form.is_valid():
                data = free_variable_form.cleaned_data
                controller = DocumentController() 
                controller.create_document(template, instance, data)

            # Redirect to a success page or any other desired view
        except Exception as e:
            # Handle the exception
            messages.error(request, f"Document error: {e}")
            # You might want to log the error or provide appropriate feedback to the user

        return redirect(request.path)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.get_object()

        # Retrieve document, important that the kwarg = id
        template_id = self.kwargs["template_id"]
        template = DocumentTemplate.objects.get(pk=template_id)

        context["document_template"] = template
        context["free_variable_form"] = FreeVariableForm(document_template=template)

        # Retrieve file
        file_queryset = File.objects.filter(
            meta__document_template=template_id,
            object_id=instance.pk,
            content_type_id=ContentType.objects.get_for_model(self.model),
        ).order_by("-datetime_created")

        context["file_list"] = file_queryset

        return context




@router.bloomerp_route(
    models = DocumentTemplate, 
    path="editor",
    route_type="detail", 
    name="Editor",
    url_name="editor",
    description="Document Template Editor"
    )
class BloomerpDocumentTemplateEditorView(BloomerpBaseDetailView, UpdateView):
    model = DocumentTemplate
    template_name = "document_template_views/bloomerp_document_template_editor_view.html"
    fields = ["template"]

    

