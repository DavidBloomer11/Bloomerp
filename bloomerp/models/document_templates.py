from django.db import models
from django.contrib.contenttypes.models import ContentType
from bloomerp.models.core import BloomerpModel, ApplicationField
from bloomerp.models.fields import CodeField, TextEditorField
from django.utils.translation import gettext_lazy as _

# ---------------------------------
# Document Template Model
# ---------------------------------
class DocumentTemplateHeader(BloomerpModel):
    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = 'bloomerp_document_template_header'

    name = models.CharField(
        max_length=100,
        blank=False,
        null=False, 
        help_text=_("Name of the template header.")) #Name of the document template header
    header = models.ImageField(
        help_text=_("Image of the header."),
        upload_to='document_templates/headers',
    ) 
    #Content of the header
    
    def __str__(self):
        return self.name
    
# ---------------------------------
# Document Template Free Variable Model
# ---------------------------------
class DocumentTemplateFreeVariable(BloomerpModel):
    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = 'bloomerp_document_template_free_variable'

    VARIABLE_TYPE_CHOICES = [
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('text', 'Text'),
        ('list', 'List'),
        ('integer', 'Integer'),
        ('float', 'Decimal'),
        ('model','Model')
    ]
    
    name = models.CharField(max_length=100, blank=False, null=False) #Name of the free variable
    variable_type = models.CharField(max_length=10, choices=VARIABLE_TYPE_CHOICES, blank=False, null=False)
    options = models.TextField(null=True, blank=True)
    required = models.BooleanField(null=False, blank=False, default=False)

    @property
    def slug(self):
        return self.name.replace(' ','_').lower()
    
    def __str__(self):
        return self.name
    

# ---------------------------------
# Document Template Styling Model
# ---------------------------------
class DocumentTemplateStyling(BloomerpModel):
    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = 'bloomerp_document_template_styling'

    name = models.CharField(max_length=100, blank=False, null=False) #Name of the document template styling
    styling = CodeField(language='css', default='') #Content of the styling
    
    def __str__(self):
        return self.name


# ---------------------------------
# Document Template Model
# ---------------------------------
class DocumentTemplate(BloomerpModel):
    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = 'bloomerp_document_template'

    name = models.CharField(max_length=100, blank=False, null=False) #Name of the document template
    template = TextEditorField(default='') # Content of the template, including the variables
    model_variable = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True) # Many to many field to Content Type
    free_variables = models.ManyToManyField(DocumentTemplateFreeVariable,blank=True) # Many to many field of free variable, a free variable is a variable that is not from a model
    template_header = models.ForeignKey(DocumentTemplateHeader, on_delete=models.SET_NULL, null=True, blank=True) #Foreign key to the document template header
    footer = models.TextField(null=True,blank=True)
    standard_document = models.BooleanField(null=False,blank=False, default=False) # Signifies weather the document should be created on object creation
    styling = models.ForeignKey(DocumentTemplateStyling, on_delete=models.SET_NULL, null=True, blank=True) # Foreign key to the document template styling

    def __str__(self):
        return self.name

    allow_string_search = True
    string_search_fields = ['name']

    def get_related_content_types(model):
        related_content_types = [ContentType.objects.get_for_model(model)]
        return related_content_types

    @property
    def application_fields(self):
        '''
        Returns a queryset of ApplicationField that are related to the model variable of the document template.
        '''
        qs = ApplicationField.objects.filter(content_type=self.model_variable)
        return qs

    @staticmethod
    def get_standard_documents_for_instance(instance):
        content_type = ContentType.objects.get_for_model(instance)
        return DocumentTemplate.objects.filter(model_variable=content_type, standard_document=True)
    
