from typing import Any
from django.forms import ValidationError
from bloomerp.models import ApplicationField, User, File, UserDetailViewTab, Link, UserListViewPreference
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.utils import timezone
from datetime import timedelta
from django.core.files import File as DjangoFile
from django.template.loader import get_template
from django.db.models import Model
from uuid import UUID
from bloomerp.utils.models import (
    get_file_fields_dict_for_model,
    get_bloomerp_file_fields_for_model,
    get_foreign_key_fields_for_model
    )
from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField as DefaultJSONField
# ---------------------------------
# Bloomerp Bulk Upload Form
# ---------------------------------
class BulkUploadForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(BulkUploadForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                self.fields[name].widget = forms.Select(choices=[(True, 'True'), (False, 'False')])

        # Add delete all objects
        self.fields['delete_all'] = forms.BooleanField(required=False, label='Delete all selected objects',initial=False)

        # Remove last_updated_by field
        if 'last_updated_by' in self.fields:
            del self.fields['last_updated_by']

# ---------------------------------
# Object file form
# ---------------------------------

class ObjectFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['name', 'file']

    def __init__(self,
                 related_object:Model=None,
                 user:User=None,
                *args, **kwargs):

        self.related_object = related_object
        self.user = user

        super().__init__(*args, **kwargs)


    def save(self, commit=True):
        # Override the save method to set the content_type and object_id
        instance:File = super().save(commit=False)

        if self.related_object:
            instance.content_type = ContentType.objects.get_for_model(self.related_object)
            instance.object_id = self.related_object.pk
    
        if self.user:
            instance.uploaded_by = self.user


        if commit:
            instance.save()
        return instance

# ---------------------------------
# Bloomerp Model Form
# ---------------------------------
from bloomerp.widgets.foreign_key_widget import ForeignKeyWidget
from bloomerp.widgets.code_editor_widget import AceEditorWidget
from bloomerp.widgets.multiple_model_select_widget import MultipleModelSelect
from django.forms.widgets import DateInput, DateTimeInput


class BloomerpModelForm(forms.ModelForm):
    model:Model = None
    user:User = None
    instance:Model = None
    is_new_instance:bool = True

    def __init__(self, model:Model, user:User=None, *args, **kwargs):
        
        # Set the model instance to the form instance
        self.model = model
        self._meta.model = model
        self.user = user

        super(BloomerpModelForm, self).__init__(*args, **kwargs)

        # Set the instance to the form instance
        instance:Model = kwargs.get('instance')
        if instance:
            self.instance = instance
            self.is_new_instance = False

        # Get all of the foreign key fields for the model
        self.foreign_key_fields = get_foreign_key_fields_for_model(self.model)


        # ---------------------------------
        # FOREIGN KEY FIELDS
        # ---------------------------------
        # Update the widgets for the foreign key fields
        for field in self.foreign_key_fields:
            # Get the related model
            if field.field in self.fields:
                related_model = field.meta['related_model']
                model = ContentType.objects.get(pk=related_model).model_class()
                self.fields[field.field].widget = ForeignKeyWidget(model=model)
        
        # ---------------------------------
        # MANY TO MANY FIELDS
        # ---------------------------------
        # Update the widgets for many to many fields
        for field in self._meta.model._meta.many_to_many:
            if field.name in self.fields:
                related_model = field.remote_field.model
                self.fields[field.name].widget = MultipleModelSelect(model=related_model)
    
        # ---------------------------------
        # FILE FIELDS
        # ---------------------------------
        # Update the widgets for the file fields
        self.file_fields = get_bloomerp_file_fields_for_model(self.model, output='list')

        # ---------------------------------
        # DATE AND DATETIME FIELDS
        # ---------------------------------
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                self.fields[field_name].widget = DateInput(attrs={'type': 'date'})
            elif isinstance(field, forms.DateTimeField):
                self.fields[field_name].widget = DateTimeInput(attrs={'type': 'datetime-local'})

        # ---------------------------------
        # JSON FIELDS
        # ---------------------------------
        # Update the widgets for the json fields
        for field_name, field in self.fields.items():
            # Check if the field is a JSONField
            model_field = self._meta.model._meta.get_field(field_name)
            
            if isinstance(model_field, (JSONField, DefaultJSONField)):
                # Apply the AceEditorWidget for JSON fields
                self.fields[field_name].widget = AceEditorWidget(language='json')

        # ---------------------------------
        # Remove created_by and updated_by fields
        # ---------------------------------
        if 'created_by' in self.fields:
            del self.fields['created_by']
        if 'updated_by' in self.fields:
            del self.fields['updated_by']
                
    def save(self, commit=True):
        '''
        Saves the form instance to the database

        '''

        instance = super(BloomerpModelForm, self).save(commit=False)

        # Check if the instance is new by checking if it has no primary key
        is_new_instance = instance.pk is None

        # Mark all temporary files as finalized after successful save
        def save_file_fields():
            if not instance.pk:
                raise ValueError("Instance must be saved before saving file fields")

            for field in self.file_fields:
                file:File = self.cleaned_data.get(field, None)
                if file:
                    # There is a new file so it has to be updated
                    file.persisted = True
                    file.content_type = ContentType.objects.get_for_model(self.model)
                    file.object_id = instance.pk
                    file.updated_by = self.user
                    file.created_by = self.user
                    file.save()
                else:
                    # There is no file, so we should delete the old file if it exists
                    old_file : File = getattr(instance, field, None)
                    if old_file:
                        old_file.delete()

        if commit:
            instance.save()
            save_file_fields()
        else:
            instance.save_file_fields = save_file_fields
            instance.is_new_instance = is_new_instance
        
        return instance

    def add_prefix(self, field_name):
        """
        Return the field name with a prefix appended.
        Overrides the default if the prefix contains "__".
        """
        if self.prefix and "__" in self.prefix:
            # Use "__" as the separator if the prefix contains "__"
            return f"{self.prefix}{field_name}"
        else:
            # Default behavior: use superclass method with hyphen separator
            return super().add_prefix(field_name)

# ---------------------------------
# Bloomerp Field Select Form
# ---------------------------------    
class BloomerpDownloadBulkUploadTemplateForm(forms.Form):
    file_type = forms.ChoiceField(choices=[('csv', 'CSV'), ('xlsx', 'Excel')])

    def __init__(self, model: Model = None, *args, **kwargs):
        super(BloomerpDownloadBulkUploadTemplateForm, self).__init__(*args, **kwargs)
        # Check if the content_type_id is provided in the request.POST
        content_type_id = kwargs.get('data', {}).get('content_type_id', None)
        if content_type_id:
            try:
                self.model = ContentType.objects.get(pk=content_type_id).model_class()
                print("Model:", self.model)
            except ContentType.DoesNotExist:
                self.model = None
                print("ContentType with id", content_type_id, "does not exist.")
        elif model:
            self.model = model
        else:
            raise ValueError("Model or content_type_id must be provided")

        if not self.model:
            raise ValueError("Model could not be determined.")

        # Init skip fields
        skip_fields = [
            'created_by',
            'updated_by',
            'datetime_created',
            'datetime_updated',
        ]

        # Model fields
        self.model_fields = []


        # Create model form and copy the fields
        ModelForm = modelform_factory(self.model, exclude=skip_fields)
        form_instance = ModelForm()

        # Add the fields to the form
        for field_name, field in form_instance.fields.items():
            self.fields[field_name] = forms.BooleanField(
                label=field.label,
                required=field.required,
                initial=field.required,
                disabled=field.required,
                help_text=field.help_text
            )

            # Add the field to the model fields
            self.model_fields.append(field_name)

        # Add content type id as hidden field
        self.fields['content_type_id'] = forms.IntegerField(widget=forms.HiddenInput(), initial=ContentType.objects.get_for_model(self.model).pk)

    def get_selected_fields(self):
        # Run the clean method to get the selected fields
        if self.is_valid():
            # Only include fields that are checked and in the model fields
            return [field for field in self.model_fields if self.cleaned_data.get(field, False)]
        return []
    

    

# ---------------------------------
# Bloomerp Bloomerp Model Form
# ---------------------------------
from bloomerp.models import File
class BloomerpModelFormDepr(forms.ModelForm):
    model:Model = None
    instance = None
    help_text_template = 'snippets/help_text_snippet.html'
    user:User = None
    form_name:str = None
    exception_models = ['file','contenttype']

    def __init__(self, user:User=None, *args, **kwargs):
        super(BloomerpModelFormDepr, self).__init__(*args, **kwargs)

        # Get instance from the form
        instance = kwargs.get('instance')

        # Set the form name 
        self.form_name = self._meta.model.__name__

        # Get the prefix from the form
        prefix = kwargs.get('prefix', None)

        # Set the instance to the form instance
        if instance:
            self.instance = instance


        if user and hasattr(user, 'get_content_types_for_user'):
            # Set the user to the form instance
            self.user = user

            # Get all of the different content types that the user has access to
            update_content_types = user.get_content_types_for_user(['change'])
            create_content_types = user.get_content_types_for_user(['add'])
        else:
            # This is a temporary solution to avoid errors when the user is not provided
            update_content_types = ContentType.objects.none()
            create_content_types = ContentType.objects.none()
            

        # Set the model instance to the form instance
        self.model = self._meta.model

        # Get the content type of the model
        content_type = ContentType.objects.get_for_model(self.model)
        file_content_type = ContentType.objects.get_for_model(File)

        # Get the application fields for the model
        self.application_fields = ApplicationField.objects.filter(content_type=content_type)

        # Get the file fields for the model
        file_fields_dict = get_file_fields_dict_for_model(self.model)

        self.file_fields = [field['name'] for field in file_fields_dict]

        # Add the file fields to the form
        for file_field in file_fields_dict:
            allowed_extensions = ', '.join(file_field['allowed_extensions'])
            attrs = {'class': 'form-control', 'accept': allowed_extensions}

            if instance:
                file_instance : File = getattr(instance, file_field['name'], None)
                if file_instance:
                    # Add the file field to the form
                    
                    self.fields[file_field['name']] = forms.FileField(required=file_field['required'], initial=file_instance.file, widget=forms.FileInput(attrs=attrs))
                    self.fields[file_field['name']].help_text = f'Current file: <a href="{file_instance.path}">{file_instance.name}</a> </br>Allowed extensions: {allowed_extensions}'
                else:
                    self.fields[file_field['name']] = forms.FileField(required=file_field['required'], widget=forms.FileInput(attrs=attrs))
                    self.fields[file_field['name']].help_text = f'Allowed extensions: {allowed_extensions}'
            else:
                self.fields[file_field['name']] = forms.FileField(required=file_field['required'], widget=forms.FileInput(attrs=attrs))
                self.fields[file_field['name']].help_text = f'Allowed extensions: {allowed_extensions}'
        
        # Get exception content types
        exception_content_types = self.get_exception_content_types().values_list('pk', flat=True)

        # Get foreign key fields for the model
        self.foreign_key_fields = self.application_fields.filter(field_type='ForeignKey').exclude(meta__related_model__in=exception_content_types).exclude(field='last_updated_by')

        # Add the foreign key fields to the form
        for foreign_key_field in self.foreign_key_fields:
            # Get the field name
            field = foreign_key_field.field
            
            if field not in self.fields.keys():
                continue

            # Set permissions
            create, update = False, False

            # Get the related model id, model and form
            related_model_id = foreign_key_field.meta['related_model']
            related_content_type = ContentType.objects.get(pk=related_model_id)
            ForeignModel = related_content_type.model_class()
            ForeignModelForm = modelform_factory(ForeignModel, exclude=['last_updated_by','user','avatar'], form=forms.ModelForm)            
            
            if related_content_type in create_content_types:
                create = True
                # Add create new item form
                create_form = ForeignModelForm(prefix=f'create_{field}')

                # Update fields
                updated_fields = {f'create_{field}_' + key: value for key, value in create_form.fields.items()}

                # Add the form to the form fields
                self.fields.update(updated_fields)

                for key, value in updated_fields.items():
                    self.fields[key].required = False
                    self.fields[key].widget.attrs['style'] = 'display: none;'
                    self.fields[key].label = ''
                    self.fields[key].help_text = ''

            # Check if user has update permission
            if related_content_type in update_content_types and instance and getattr(instance, field, None):
                update = True

                # Add update form
                update_form = ForeignModelForm(instance=getattr(instance, field), prefix=f'update_{field}')
                
                # Add update_field_id to the form
                update_form.fields[f'{field}_id'] = forms.IntegerField(widget=forms.HiddenInput(), initial=getattr(instance, field).pk)


                # Update fields & initial
                update_form.fields = {f'update_{field}_' + key: value for key, value in update_form.fields.items()}
                update_form.initial = {f'update_{field}_' + key: value for key, value in update_form.initial.items()}

                

                # Add the form to the form fields
                self.fields.update(update_form.fields)
                self.initial.update(update_form.initial)
                for key, value in update_form.fields.items():
                    self.fields[key].required = False
                    self.fields[key].widget.attrs['style'] = 'display: none;'
                    self.fields[key].label = ''
                    self.fields[key].help_text = ''
            
            
            # Add help text to the field
            self.fields[field].help_text = self.get_help_text(field, create, update, prefix)
                
        # Remove last_updated_by field
        if 'last_updated_by' in self.fields:
            del self.fields['last_updated_by']

    def get_exception_content_types(self):
        '''
        Returns the content types that should not be included in the foreign key fields
        '''
        return ContentType.objects.filter(model__in=self.exception_models)

    def get_content_type(self):
        '''
        Returns the content type of the model
        '''
        return ContentType.objects.get_for_model(self.model)

    def get_user(self):
        '''
        Returns the user that the form is associated with
        '''
        return self.user

    def get_help_text(self, field, create=False, update=False, prefix=None):
        '''
        Generates help text for the foreign key field
        '''
        if prefix is not None:
            prefix = prefix + '-'
        else:
            prefix = ''

        context = {
            'create' : create,
            'update' : update,
            'field' : field,
            'prefix' : prefix
        }

        template = get_template(self.help_text_template)
        help_text = template.render(context)
        
        return help_text

    def clean(self):
        cleaned_data = super().clean()

        # Handle file fields
        for field in self.file_fields:
            file = cleaned_data.get(field, None)
            
            if file and type(file) != UUID:
                # In this case the file is a new file
                try:
                    file = DjangoFile(file)
                    file_instance = self.clean_file_field(file, field)
                    cleaned_data[field] = file_instance
                except ValidationError as e:
                    self.add_error(field, e)
            elif file and type(file) == UUID:
                try:
                    cleaned_data[field] = File.objects.get(pk=file)
                except File.DoesNotExist:
                    self.add_error(field, ValidationError("File does not exist"))
                
        # Handle foreign key fields
        for foreign_key_field in self.foreign_key_fields:
            field_name = foreign_key_field.field

            create, update = False, False

            # Check if create / update checkbox is checked
            if self.data.get(f'create_{field_name}_checkbox', False) == 'on':
                create = True
            
            if self.data.get(f'update_{field_name}_checkbox', False) == 'on':
                update = True
            
            
            if create and update:
                raise ValidationError(f"Cannot create and update {field_name} at the same time")

            create_prefix = f'create_{field_name}_'
            update_prefix = f'update_{field_name}_'
            create_data = {key[len(create_prefix):]: val for key, val in cleaned_data.items() if key.startswith(create_prefix) and val}
            update_data = {key[len(update_prefix):]: val for key, val in cleaned_data.items() if key.startswith(update_prefix) and val}

            # Create a new instance only if data is provided
            if create_data and any(create_data.values()) and create:
                try:
                    cleaned_data[field_name] = self.clean_create_foreign_key(field_name, create_data)
                except ValidationError as e:
                    self.add_error(field_name, e)

            # Update existing instance only if changes are made
            elif update_data and any(update_data.values()) and update:
                try:
                    cleaned_data[field_name] = self.clean_update_foreign_key(field_name, update_data)
                except ValidationError as e:
                    self.add_error(field_name, e)
            # If neither create nor update is checked, the field should just be the selected instance
            # No need to do anything here

        return cleaned_data

    def clean_file_field(self, file:DjangoFile, file_field:str):
        # First check if the file is already associated with the instance
        if self.instance and getattr(self.instance, file_field, None):
            file_instance:File = getattr(self.instance, file_field)
            file_instance.file = file
            file_instance.name = file.name
            file_instance.save()
            
        else:
            if self.instance is None: 
                object_id = None
            else:
                object_id = self.instance.pk
            
            # Check if the file already exists
            # Get the datetime and makse sure that the file hasn't been uploaded in the last 60 minutes
            # This is to prevent the same file from being uploaded multiple times, which can happen when using django-formtools
            now = timezone.now()
            time_threshold = now - timedelta(minutes=60)

            file_instance = File.objects.filter(name=file.name,
                                                created_by=self.user,
                                                datetime_created__gte=time_threshold,
                                                object_id=object_id,
                                                ).first()
            if file_instance:
                return file_instance
            else:
                file_instance = File.objects.create(
                    created_by=self.user,
                    file=file,
                    name=file.name,
                    content_type=self.get_content_type(),
                    object_id=object_id
                )
        
        return file_instance

    def clean_create_foreign_key(self, field_name, data):
        ForeignModel:Model = self.fields[field_name].queryset.model
        ForeignModelForm = modelform_factory(ForeignModel, exclude=['last_updated_by', 'user'])
        form = ForeignModelForm(data=data,files=data)

        if form.is_valid():
            data = form.data
            # Prevent model from saving multiple times
            qs = ForeignModel.objects.filter(**data)
            if qs.exists():
                return qs.first()
            else:
                return form.save()

        else:
            raise ValidationError(f"Error creating new {ForeignModel.__name__}: {form.errors}")

    def clean_update_foreign_key(self, field_name, data):
        instance_id = data.get(f'{field_name}_id')

        ForeignModel = self.fields[field_name].queryset.model
        instance = ForeignModel.objects.get(pk=instance_id)
        ForeignModelForm = modelform_factory(ForeignModel, exclude=['last_updated_by', 'user', 'avatar'])
        form = ForeignModelForm(data, instance=instance)
        if form.is_valid():
            return form.save()
        else:
            raise ValidationError(f"Error updating {ForeignModel.__name__}: {form.errors}")
                 
    def save(self, commit=True):
        # Call the base class save method
        instance = super(BloomerpModelFormDepr, self).save(commit=commit)

        # Check if the instance is new by checking if it has no primary key
        is_new_instance = instance.pk is None

        # Assign the instance to self.instance for further processing
        self.instance = instance

        def update_file_fields():
            for field in self.file_fields:
                file = self.cleaned_data.get(field, None)
                if file:
                    file_instance = File.objects.get(pk=file.pk)
                    file_instance.content_type = self.get_content_type()
                    file_instance.object_id = self.instance.pk
                    file_instance.save()

        if is_new_instance and commit:
            update_file_fields()
        
        # If the instance is new and commit is False, we need to update the file fields after the instance has been saved
        elif is_new_instance and not commit:
            self.update_file_fields = update_file_fields
            instance.update_file_fields = update_file_fields
            instance.is_new_instance = is_new_instance
        
        return instance
    

# ---------------------------------
# Links select form
# ---------------------------------
class DetailLinksSelectForm(forms.Form):
    def __init__(self, content_type:ContentType, user:User, *args, **kwargs):
        super(DetailLinksSelectForm, self).__init__(*args, **kwargs)
        
        # Get all of the links that are available for the content type
        qs = Link.objects.filter(content_type=content_type, level='DETAIL') 
        
        for link in qs:
            if link.number_of_args() > 1:
                # Exclude links that require more than one argument
                qs = qs.exclude(pk=link.pk)
        
        # Get the links that the user has access to
        detail_view_links = UserDetailViewTab.get_detail_view_tabs(content_type=content_type, user=user).values_list('link_id', flat=True)

        self.fields['links'] = forms.ModelMultipleChoiceField(
            queryset=qs,
            widget=forms.CheckboxSelectMultiple
        )

        self.fields['links'].initial = detail_view_links

        # Add content type id as hidden field
        self.fields['content_type_id'] = forms.IntegerField(widget=forms.HiddenInput(), initial=content_type.pk)

        self.user = user


    def save(self) -> None:
        content_type_id = self.cleaned_data.get('content_type_id')
        content_type = ContentType.objects.get(pk=content_type_id)
        links = self.cleaned_data.get('links')

        # Get existing UserDetailViewTab objects for the user and content type
        existing_tabs = UserDetailViewTab.objects.filter(user=self.user, link__content_type=content_type)

        # Determine which links need to be added and which need to be removed
        existing_link_ids = set(existing_tabs.values_list('link_id', flat=True))
        selected_link_ids = set(links.values_list('id', flat=True))

        # Links to add
        links_to_add = selected_link_ids - existing_link_ids
        # Links to remove
        links_to_remove = existing_link_ids - selected_link_ids

        # Add new UserDetailViewTab objects
        for link_id in links_to_add:
            UserDetailViewTab.objects.create(user=self.user, link_id=link_id)

        # Remove UserDetailViewTab objects
        UserDetailViewTab.objects.filter(user=self.user, link_id__in=links_to_remove).delete()

        print("Links saved")


class ListViewFieldsSelectForm(forms.Form):
    def __init__(self, content_type:ContentType, user:User, *args, **kwargs):
        super(ListViewFieldsSelectForm, self).__init__(*args, **kwargs)
        
        # Get all of the Application fields that are available for the content type
        qs = ApplicationField.objects.filter(content_type=content_type)
        
        
        # Get the links that the user has access to
        application_fields = UserListViewPreference.objects.filter(user=user, application_field__in=qs).values_list('application_field_id', flat=True)
        
        self.fields['fields'] = forms.ModelMultipleChoiceField(
            queryset=qs,
            widget=forms.CheckboxSelectMultiple
        )

        self.fields['fields'].initial = application_fields

        # Add content type id as hidden field
        self.fields['content_type_id'] = forms.IntegerField(widget=forms.HiddenInput(), initial=content_type.pk)

        self.user = user


    def save(self) -> None:
        content_type_id = self.cleaned_data.get('content_type_id')
        content_type = ContentType.objects.get(pk=content_type_id)
        fields = self.cleaned_data.get('fields')

        # Get existing UserListViewPreference objects for the user and content type
        existing_preferences = UserListViewPreference.objects.filter(user=self.user, application_field__content_type=content_type)

        # Determine which fields need to be added and which need to be removed
        existing_field_ids = set(existing_preferences.values_list('application_field_id', flat=True))
        selected_field_ids = set(fields.values_list('id', flat=True))

        # Fields to add
        fields_to_add = selected_field_ids - existing_field_ids
        # Fields to remove
        fields_to_remove = existing_field_ids - selected_field_ids

        # Add new UserListViewPreference objects
        for field_id in fields_to_add:
            UserListViewPreference.objects.create(user=self.user, application_field_id=field_id)

        # Remove UserListViewPreference objects
        UserListViewPreference.objects.filter(user=self.user, application_field_id__in=fields_to_remove).delete()

