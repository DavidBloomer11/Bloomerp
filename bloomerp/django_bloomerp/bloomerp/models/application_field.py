from __future__ import annotations

from django import forms
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db.models.query import QuerySet
from typing import Any, Optional, Type
from django.utils.encoding import force_str
from django.utils.translation import gettext, gettext_lazy as _
from bloomerp.field_types.types import FieldType

class ApplicationField(models.Model):
    """
    An ApplicationField is a model that stores information 
    about fields and attributes in the Django model.
    
    It is used throughout the application to provide metadata
    about fields, such as their type, related model (if any),
    and other useful information.
    """
    class Meta:
        verbose_name = _("Application Field")
        verbose_name_plural = _("Application Fields")
        managed = True
        db_table = "bloomerp_application_field"
    
    allow_string_search = False

    field = models.CharField(
        max_length=100,
        help_text=_("The name of the field."),
        verbose_name=_("Field"),
        )
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        help_text=_("The content type (model) this field belongs to."),
        verbose_name=_("Content Type"),
    )
    field_type = models.CharField(
        max_length=100, 
        choices=FieldType.choices(),
        help_text=_("The type of the field."),
        verbose_name=_("Field Type"),
        )
    related_model = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='related_models', 
        help_text=_("Related model for ForeignKey, OneToOneField, ManyToManyField"),
        verbose_name=_("Related Model"),
    )
    meta = models.JSONField(
        null=True, 
        blank=True,
        help_text=_("Additional metadata about the field."),
        verbose_name=_("Meta"),
        )

    # Database related fields
    db_table = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text=_("The database table this field belongs to."),
        verbose_name=_("DB Table"),
    )
    db_field_type = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name=_("DB Field Type"),
        )
    db_column = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name=_("DB Column"),
        )

    def __str__(self):
        return self.content_type.__str__() + " | " + str(self.field)


    def get_field_type_enum(self) -> FieldType:
        """Returns the FieldType enum for this application field."""
        declared_field_type = None
        try:
            declared_field_type = FieldType.from_id(self.field_type)
        except ValueError:
            declared_field_type = None

        try:
            model_field = self._get_model_field()
        except FieldDoesNotExist:
            if declared_field_type is None:
                raise
            return declared_field_type

        model_backed_field_type = FieldType.from_model_field_cls(model_field.__class__)

        if (
            model_backed_field_type is not None
            and model_backed_field_type.model_field_cls == model_field.__class__
            and (
                declared_field_type is None
                or declared_field_type.model_field_cls != model_field.__class__
            )
        ):
            return model_backed_field_type

        if declared_field_type is not None:
            return declared_field_type

        if model_backed_field_type is not None:
            return model_backed_field_type

        raise ValueError(f"Unknown field type: {self.field_type}")


    def get_for_model(model:models.Model) -> QuerySet['ApplicationField']:
        """Returns application fields for a specific model"""
        return (
            ApplicationField.objects.filter(
                content_type=ContentType.objects.get_for_model(model)
            )
            .select_related("content_type", "related_model")
        )
        
    @staticmethod
    def get_by_field(model:models.Model, field_name:str) -> Optional['ApplicationField']:
        """Returns an application field for a specific model and field name"""
        try:
            return ApplicationField.objects.get(
                content_type=ContentType.objects.get_for_model(model),
                field=field_name
            )
        except ApplicationField.DoesNotExist:
            return None

    @classmethod
    def resolve_for_content_type(
        cls,
        content_type: ContentType,
        field: str | "ApplicationField",
    ) -> "ApplicationField":
        """Resolve a field name or ApplicationField within a content type.

        Args:
            content_type: The content type that must own the field.
            field: A field name or an existing ApplicationField instance.

        Returns:
            The resolved ApplicationField.

        Raises:
            TypeError: If the arguments have unsupported types.
            ValueError: If the field does not exist or belongs to another
                content type.
        """
        if not isinstance(content_type, ContentType):
            raise TypeError("content_type must be a ContentType instance")

        if isinstance(field, cls):
            application_field = field
        elif isinstance(field, str) and field.strip():
            field_name = field.strip()
            try:
                application_field = cls.objects.get(
                    content_type=content_type,
                    field=field_name,
                )
            except cls.DoesNotExist as exc:
                raise ValueError(
                    f"Unknown field '{field_name}' for '{content_type}'"
                ) from exc
        else:
            raise TypeError("field must be a field name or ApplicationField instance")

        if application_field.content_type_id != content_type.id:
            raise ValueError(
                f"Field '{application_field.field}' belongs to a different content type"
            )
        return application_field

    
    @property
    def title(self):
        try:
            model_field = self._get_model_field()
        except FieldDoesNotExist:
            return gettext(self.field.replace("_", " ").title())

        declared_label = getattr(model_field, "_verbose_name", None)
        if declared_label is not None:
            # gettext_lazy values resolve here; plain strings can still be supplied
            # by an extension app and resolved from the extracted model catalog.
            return gettext(force_str(declared_label))
        return gettext(self.field.replace("_", " ").title())
    
    @staticmethod
    def get_for_content_type_id(content_type_id: int) -> QuerySet:
        """Retrieves the application fields for a particular content type ID.

        Args:
            content_type_id (int): the content type ID

        Returns:
            QuerySet: the application fields
        """
        return (
            ApplicationField.objects.filter(
                content_type_id=content_type_id
            )
            .select_related("content_type", "related_model")
        )

    def get_model(self) -> models.Model:
        """Returns the model class for this application field."""
        return self.content_type.model_class()
    
    def get_related_model(self) -> Optional[models.Model]:
        """Returns the related model class for this application field, if any."""
        if self.related_model:
            return self.related_model.model_class()
        try:
            return getattr(self._get_model_field(), "related_model", None)
        except FieldDoesNotExist:
            return None
        return None

    def _get_model_field(self) -> models.Field:
        """Resolve the concrete Django model field for this application field.

        `ApplicationField.field` may refer to aliases such as `pk`, which are
        valid Python-level attributes on a model but not always resolvable via
        Django's `_meta.get_field()`.
        """
        model_cls = self.get_model()
        try:
            return model_cls._meta.get_field(self.field)
        except FieldDoesNotExist:
            if self.field == "pk":
                return model_cls._meta.pk
            raise
    
    def get_form_field(self) -> forms.Field:
        """Returns the form field object for this application field

        Returns:
            forms.Field: the form field object
        """
        try:
            model_field = self._get_model_field()
        except FieldDoesNotExist:
            return None

        if not hasattr(model_field, "formfield"):
            return None
        
        field_type = self.get_field_type_enum().value
        
        # If a custom form field class is defined, use it
        if field_type.form_field_cls:
            # Get the form field with custom class, but let Django handle kwargs
            form_field = model_field.formfield(form_class=field_type.form_field_cls)
        else:
            # Use Django's default formfield conversion
            form_field = model_field.formfield()
        
        if form_field is None:
            return None

        if field_type.widget_cls:
            form_field.widget = self.get_widget()

        return form_field
    
    def get_form_field_cls(self) -> Type[forms.Field]:
        """Returns the form class for this application field

        Returns:
            Type[forms.Field]: the form class for this model
        """
        field_type = self.get_field_type_enum().value
        return field_type.form_field_cls
           
    def get_widget(self, layout_config: dict[str, Any] | None = None) -> forms.Widget:
        """Retursn the widget for this application field

        Returns:
            forms.Widget: the widget object
        """
        field_type = self.get_field_type_enum().value
        return field_type.build_widget(self, layout_config=layout_config)
    
    @property
    def icon(self):
        return self.get_field_type_enum().value.icon
        
        
    @property
    def field_type_enum(self):
        return self.get_field_type_enum()
    
    
