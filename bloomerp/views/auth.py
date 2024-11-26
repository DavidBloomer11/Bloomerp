from typing import Any
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from bloomerp.forms.auth import UserDetailViewPreferenceForm, UserDetailViewPreferenceFormset
from bloomerp.forms.core import ListViewFieldsSelectForm
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from bloomerp.views.mixins import HtmxMixin
from bloomerp.models import (
    UserDetailViewPreference,
    User
    )
from bloomerp.utils.models import model_name_plural_underline
from django.contrib.auth.mixins import PermissionRequiredMixin


# -------------------------------------------
# NEW SHIT
from bloomerp.utils.router import BloomerpRouter
from bloomerp.views.mixins import HtmxMixin, BloomerpModelContextMixin
from bloomerp.views.mixins import BloomerpModelFormViewMixin
from bloomerp.views.core import BloomerpBaseDetailView
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic.edit import FormView, UpdateView
from django.contrib.auth import update_session_auth_hash


class ProfileMixin:
    tabs = [
        {"name":"Details", "url":"users_my_profile_overview", "requires_pk":False},
        {"name":"Change password", "url":"users_my_profile_change_password", "requires_pk":False},
        {"name":"List view preferences", "url":"users_my_profile_list_view_preference","requires_pk":False},
        {"name":"Detail view preferences", "url":"users_my_profile_detail_view_preference","requires_pk":False}
    ]
    exclude_header = True

    extra_context = {"disable_tab_select":True, "tabs":tabs}

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)
    model = User

router = BloomerpRouter()

@router.bloomerp_route(
    path="my-profile/",
    models=User,
    route_type="list",
    name="Profile",
    description="Overview of profile",
    url_name="my_profile_overview"
)
class BloomerpProfileView(BloomerpModelFormViewMixin, ProfileMixin, HtmxMixin, BloomerpModelContextMixin, UpdateView):
    template_name = 'auth_views/profile_overview.html'
    fields = ['first_name', 'last_name', 'date_view_preference', 'datetime_view_preference', 'avatar']
    success_url = reverse_lazy('users_my_profile_overview')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)
    
    

@router.bloomerp_route(
    path="my-profile/reset-password/",
    models=User,
    route_type="list",
    name="Reset password",
    description="Reset password for a user",
    url_name="my_profile_change_password"
)
class BloomerpProfilePasswordResetView(ProfileMixin, BloomerpBaseDetailView, FormView):
    template_name = 'auth_views/profile_password_reset.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users_my_profile_overview')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form:PasswordChangeForm):
        self.object = self.get_object()
        form.save()
        update_session_auth_hash(self.request, form.user)  # Prevents logout
        return super().form_valid(form)    
    
    def form_invalid(self, form):
        self.object = self.get_object()
        return super().form_invalid(form)
    

@router.bloomerp_route(
    path="my-profile/list-view-preference/",
    models=User,
    route_type="list",
    name="List view preference",
    description="List view preference for a user",
    url_name="my_profile_list_view_preference"
)
class UserListViewPreferenceView(ProfileMixin, BloomerpBaseDetailView):
    template_name = 'user_views/list_view_preference_view.html'
    permission_required = ['users.change_userlistviewpreference']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content_type_list = ContentType.objects.all()
        content_type_id = self.request.GET.get('content_type_id',None)

        
        if content_type_id:
            context['selected_model'] = ContentType.objects.get(pk=int(content_type_id)).model

            form = ListViewFieldsSelectForm(
                content_type=ContentType.objects.get(pk=content_type_id),
                user=self.request.user)
            
            context['form'] = form

        context['content_type_list'] = content_type_list
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        content_type_id = request.GET.get('content_type_id',None)
        return_to = request.GET.get('return_to',None)

        form = ListViewFieldsSelectForm(
                content_type=ContentType.objects.get(pk=content_type_id),
                user=self.request.user,
                data=request.POST
            )
        
        if form.is_valid():
            form.save()
            messages.success(self.request, 'Preferences saved successfully.')
            if return_to:
                return redirect(return_to)
            else:
                return redirect(reverse('list_view_preference') + f'?content_type_id={content_type_id}')
        else:
            return render(request, self.template_name, {'form': form})

        
@router.bloomerp_route(
    path="my-profile/detail-view-preferences/",
    models=User,
    route_type="list",
    name="Detail view preference",
    description="Detail view preference for a user",
    url_name="my_profile_detail_view_preference"
)
class UserDetailViewPreferenceView(ProfileMixin, BloomerpBaseDetailView):
    template_name = 'user_views/bloomerp_detail_view_preference_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        content_type_id = self.request.GET.get('content_type_id',None)

        list = UserDetailViewPreference.get_application_fields_info(content_type_id,self.request.user)

        Formset = formset_factory(UserDetailViewPreferenceForm, formset=UserDetailViewPreferenceFormset,extra=0)
        
        formset = Formset(initial=list)

        context['formset'] = formset
        context['content_type_list'] = ContentType.objects.all()
        if content_type_id:
            context['selected_model'] = ContentType.objects.get(pk=int(content_type_id)).model

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        content_type_id = request.GET.get('content_type_id',None)
        
        return_to = request.GET.get('return_to',None)

        Formset = formset_factory(UserDetailViewPreferenceForm, formset=UserDetailViewPreferenceFormset)


        formset = Formset(request.POST)

        if formset.is_valid():
            formset.user = self.request.user
            formset.save()
            messages.success(self.request, 'Preferences saved successfully.')
            if return_to:
                return redirect(return_to)
            else:
                return redirect(reverse('detail_view_preference') + f'?content_type_id={content_type_id}')
        else:
            return render(request, self.template_name, {'formset': formset})


from bloomerp.forms.auth import BloomerpUserCreationForm
from django.contrib.messages.views import SuccessMessageMixin
@router.bloomerp_route(
    path="create",
    name="Create user",
    url_name="add",
    description="Create a new object from User",
    route_type="list",
    models=User
)
class UserCreateView(
        PermissionRequiredMixin, 
        SuccessMessageMixin,
        HtmxMixin,
        FormView):
    template_name = "create_views/bloomerp_create_view.html"
    fields = None
    model = None
    exclude = []
    success_message = "Object was created successfully."
    form_class = BloomerpUserCreationForm
    success_url = reverse_lazy("users_list")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.verbose_name
        context["model_name_plural"] = self.model._meta.verbose_name_plural
        context["list_view_url"] = model_name_plural_underline(self.model) + "_list"
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_permission_required(self):
        return [f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"]

    def get_success_message(self, cleaned_data):
        return f"User was created successfully."

