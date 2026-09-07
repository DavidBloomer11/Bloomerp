import re
from typing import Type

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Model
from django.utils.crypto import get_random_string

from bloomerp.auth import get_login_identifier
from bloomerp.models.access_control.policy import Policy
from bloomerp.router import router
from bloomerp.views.generic.detail.base import BaseBloomerpDetailView
from bloomerp.widgets.foreign_field_widget import ForeignFieldWidget


User = get_user_model()
AUDIT_USER_FIELD_NAMES = {"created_by", "updated_by"}


def models_with_user_field() -> list[Type[Model]]:
    """Returns models with a concrete relation to the configured user model."""
    matched_models = []

    for model in apps.get_models():
        if get_user_relation_fields(model):
            matched_models.append(model)

    return matched_models


def get_user_relation_fields(model: Type[Model]) -> list:
    fields = []
    for field in model._meta.get_fields():
        if (
            getattr(field, "concrete", False)
            and field.name not in AUDIT_USER_FIELD_NAMES
            and (getattr(field, "many_to_one", False) or getattr(field, "one_to_one", False))
            and field.related_model == User
        ):
            fields.append(field)
    return fields


def get_user_relation_field(model: Type[Model]):
    fields = get_user_relation_fields(model)
    return fields[0] if fields else None


def get_email_like_value(obj) -> str:
    for field in obj._meta.get_fields():
        if not getattr(field, "concrete", False):
            continue

        field_name = getattr(field, "name", "")
        if "email" not in field_name.lower():
            continue

        value = getattr(obj, field_name, "")
        if value and "@" in str(value):
            return str(value).strip()

    return ""


def normalize_username(value: str) -> str:
    username = re.sub(r"[^a-z0-9_@.+-]", "", value.lower().replace(" ", ""))
    return username[:120] or "user"


def unique_username(seed: str) -> str:
    base = normalize_username(seed)
    username = base
    suffix = 1

    while User._default_manager.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base}{suffix}"

    return username


class CreateUserForObjectForm(forms.Form):
    relation_field = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class": "select w-full",
            }
        )
    )
    identifier = forms.CharField(
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "class": "input w-full",
                "autocomplete": "off",
            }
        )
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=ForeignFieldWidget(
            model=Group,
            attrs={
                "is_m2m" : True,
                "class" : "input w-full",
            }
        )
    )
    policies = forms.ModelMultipleChoiceField(
        queryset=Policy.objects.none(),
        required=False,
        widget=ForeignFieldWidget(
            model=Policy,
            attrs={
                "is_m2m" : True,
                "class" : "input w-full",
            }
        )
    )

    def __init__(self, *args, obj, relation_fields, **kwargs):
        self.obj = obj
        self.relation_fields = {field.name: field for field in relation_fields}
        super().__init__(*args, **kwargs)

        login_identifier = get_login_identifier()
        self.fields["relation_field"].label = "User field"
        self.fields["relation_field"].choices = [
            (field.name, str(field.verbose_name).title())
            for field in relation_fields
        ]
        self.fields["identifier"].label = "Email" if login_identifier == "email" else "Username"
        self.fields["identifier"].widget.attrs.update(
            {
                "class": "input w-full",
                "autocomplete": "off",
            }
        )
        self.fields["groups"].queryset = Group.objects.order_by("name")
        self.fields["policies"].queryset = Policy.objects.order_by("name")

        if not self.is_bound:
            self.fields["relation_field"].initial = self.get_initial_relation_field_name()
            self.fields["identifier"].initial = self.get_initial_identifier()

    def get_initial_relation_field_name(self) -> str:
        for field_name, field in self.relation_fields.items():
            if not getattr(self.obj, field.name, None):
                return field_name
        return next(iter(self.relation_fields), "")

    def get_initial_identifier(self) -> str:
        if get_login_identifier() == "email":
            return get_email_like_value(self.obj)
        return unique_username(str(self.obj))

    def clean_relation_field(self):
        field_name = self.cleaned_data["relation_field"]
        if field_name not in self.relation_fields:
            raise forms.ValidationError("Select a valid user field.")
        return field_name

    def get_selected_relation_field(self):
        field_name = self.cleaned_data.get("relation_field") if self.is_valid() else None
        if not field_name:
            field_name = self.data.get(self.add_prefix("relation_field")) or self.initial.get("relation_field")
        if not field_name:
            field_name = self.get_initial_relation_field_name()
        return self.relation_fields.get(field_name)

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()

        if get_login_identifier() == "email":
            email = identifier.lower()
            if User._default_manager.filter(email__iexact=email).exists():
                raise forms.ValidationError("A user with this email already exists.")
            return email

        if User._default_manager.filter(username__iexact=identifier).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return identifier


@router.register(
    path="create-user-for-object",
    name="Create User for Object",
    url_name="create_user_for_object",
    route_type="detail",
    models=models_with_user_field,
)
class CreateUserView(BaseBloomerpDetailView):
    template_name = "views/generic/detail/create_user_for_object.html"

    def has_permission(self):
        return self.request.user.is_superuser

    def get_object(self, queryset=None):
        if getattr(self, "object", None) is None:
            self.object = super().get_object(queryset=queryset)
        return self.object

    def get_user_relation_field(self):
        return get_user_relation_field(self.model)

    def get_user_relation_fields(self):
        return get_user_relation_fields(self.model)

    def get_form(self):
        return CreateUserForObjectForm(
            self.request.POST or None,
            obj=self.get_object(),
            relation_fields=self.get_user_relation_fields(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or self.get_form()
        relation_field = kwargs.get("relation_field") or form.get_selected_relation_field()
        related_user = getattr(self.object, relation_field.name, None) if relation_field else None
        context.update(
            {
                "form": form,
                "login_identifier": get_login_identifier(),
                "relation_field": relation_field,
                "relation_fields": self.get_user_relation_fields(),
                "related_user": related_user,
                "created_user": kwargs.get("created_user"),
                "generated_password": kwargs.get("generated_password"),
            }
        )
        return context

    def build_user_kwargs(self, identifier: str) -> dict:
        email = get_email_like_value(self.object)
        username_seed = identifier.split("@", 1)[0] if "@" in identifier else identifier
        user_kwargs = {
            "username": unique_username(username_seed or str(self.object)),
            "email": email,
        }

        if get_login_identifier() == "email":
            user_kwargs["email"] = identifier
        else:
            user_kwargs["username"] = identifier

        for attr in ("first_name", "last_name"):
            if hasattr(self.object, attr):
                user_kwargs[attr] = getattr(self.object, attr) or ""

        username_field = getattr(User, "USERNAME_FIELD", "username")
        if username_field == "email":
            user_kwargs["email"] = identifier if get_login_identifier() == "email" else email

        return user_kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form), status=400)

        relation_field = form.get_selected_relation_field()
        if relation_field is None:
            form.add_error("relation_field", "Select a valid user field.")
            return self.render_to_response(self.get_context_data(form=form), status=400)

        if getattr(self.object, relation_field.name, None):
            form.add_error("relation_field", f"{str(relation_field.verbose_name).title()} already has a linked user.")
            return self.render_to_response(
                self.get_context_data(form=form, relation_field=relation_field),
                status=409,
            )

        generated_password = get_random_string(
            16,
            allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789",
        )
        with transaction.atomic():
            user = User.objects.create_user(
                password=generated_password,
                **self.build_user_kwargs(form.cleaned_data["identifier"]),
            )
            user.groups.set(form.cleaned_data["groups"])
            for policy in form.cleaned_data["policies"]:
                policy.assign_user(user)

            setattr(self.object, relation_field.name, user)
            self.object.save(update_fields=[relation_field.name])

        
        self.add_message(
            "User account created and linked.",
            "success"
        )
        context = self.get_context_data(
            form=self.get_form(),
            relation_field=relation_field,
            created_user=user,
            generated_password=generated_password,
        )
        return self.render_to_response(context)
