from django import forms
from bloomerp.models import DocumentTemplate
from django.apps import apps

# ---------------------------------
# Free Variable Form
# ---------------------------------
class FreeVariableForm(forms.Form):
    def __init__(self, document_template: DocumentTemplate, *args, **kwargs):
        super().__init__(*args, **kwargs)

        free_variables = document_template.free_variables.all()
        for variable in free_variables:
            field_kwargs = {
                'label': variable.name,
                'required': variable.required,
            }
            if variable.variable_type == 'date':
                field_kwargs['widget'] = forms.DateInput(
                    attrs={'type': 'date'})
                field = forms.DateField(**field_kwargs)
            elif variable.variable_type == 'boolean':
                field = forms.BooleanField(**field_kwargs)

            elif variable.variable_type == 'integer':
                field = forms.IntegerField(**field_kwargs)

            elif variable.variable_type == 'float':
                field = forms.FloatField(**field_kwargs)

            elif variable.variable_type == 'text':
                field = forms.CharField(**field_kwargs)
            elif variable.variable_type == 'list':
                # Create options from choices
                options = variable.options.split(',')
                field_kwargs['choices'] = [(option, option)
                                           for option in options]

                field = forms.ChoiceField(**field_kwargs)
            elif variable.variable_type == 'model':
                # Retrieve the model
                try:
                    model = variable.options.split(',')
                    # Get the model class using the apps module without specifying app_label
                    model_class = apps.get_model(
                        app_label=model[0], model_name=model[1])

                    # Get a queryset for the model
                    queryset = model_class.objects.all()

                    # create the field
                    field = forms.ModelChoiceField(queryset=queryset)
                except:
                    # Handle the case where the model is not found
                    pass

            else:
                field = forms.CharField(**field_kwargs)

            self.fields[variable.slug] = field

