from django.db import models
import ast
from bloomerp.models.core import File
from django.core.exceptions import ValidationError
import os


# ---------------------------------
# Bloomerp File Field
# ---------------------------------
class BloomerpFileField(models.ForeignKey):
    def __init__(self, *args, allowed_extensions=None, **kwargs):
        """
        Initialize BloomerpFileField with a ForeignKey to the File model and optional file type validation.
        `allowed_extensions` specifies allowed file types; if '__all__' or None, all are allowed.
        """
        self.allowed_extensions = allowed_extensions if allowed_extensions is not None else '__all__'
        kwargs['to'] = 'bloomerp.File'
        kwargs['on_delete'] = models.SET_NULL
        kwargs['null'] = True
        kwargs['blank'] = True
        
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        """
        Specifies the default form field and widget to use with this model field.
        """
        from bloomerp.widgets.bloomerp_file_field_widget import BloomerpFileFieldWidget

        defaults = {
            'widget': BloomerpFileFieldWidget(),
        }

        defaults.update(kwargs)
        return super().formfield(**defaults)
        
    def validate_file_extension(self, file_instance:File):
        """
        Validate the file extension of the file associated with the foreign key.
        """
        # If allowed_extensions is '__all__', no restriction on file types
        if self.allowed_extensions == '__all__':
            return

        # Get the file extension of the associated file
        ext = os.path.splitext(file_instance.file.name)[1].lower()

        # Check if the extension is in the allowed list
        if ext not in self.allowed_extensions:
            allowed_ext_str = ', '.join(self.allowed_extensions)
            raise ValidationError(f'Unsupported file extension. Allowed extensions are: {allowed_ext_str}')

    def clean(self, value, model_instance):
        """
        Perform the validation on the foreign key reference and ensure the file type is allowed.
        """
        # Call the parent clean method to validate the ForeignKey relationship
        value = super().clean(value, model_instance)

        file_instance = File.objects.get(pk=value)

        # Validate the file extension of the linked file object
        if value:  # Ensure that a valid file instance is passed
            self.validate_file_extension(file_instance)

        return value

# ---------------------------------
# Bloomerp Code Field
# ---------------------------------
class CodeField(models.TextField):
    '''
    A custom model field to store code snippets with syntax highlighting.
    '''
    def __init__(self, *args, language='python', **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """
        This method tells Django how to serialize the field for migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs['language'] = self.language
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        """
        Specifies the default form field and widget to use with this model field.
        """
        from django import forms
        from bloomerp.widgets.code_editor_widget import AceEditorWidget  # Import your custom widget

        defaults = {
            'form_class': forms.CharField,
            'widget': AceEditorWidget(language=self.language),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    # Optional: Add custom validation logic if needed
    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        # Example: Add syntax validation for Python code
        if self.language == 'python':
            import ast
            try:
                ast.parse(value)
            except SyntaxError as e:
                raise ValidationError(f"Invalid Python code: {e}")


# ---------------------------------
# Bloomerp Text Editor Field
# ---------------------------------
class TextEditorField(models.TextField):
    '''Use this field to store rich text content with a text editor.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        from django import forms
        from bloomerp.widgets.text_editor import RichTextEditorWidget

        defaults = {
            'form_class': forms.CharField,
            'widget': RichTextEditorWidget(),
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
