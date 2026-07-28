from bloomerp.router import router
from bloomerp.views.generic.detail.base import BaseBloomerpDetailView

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.views.generic.edit import FormView


User = get_user_model()


@router.register(
    path='admin-reset-password/',
    models=[User],
    route_type='detail',
    name='Reset password for user (admin)',
    url_name='admin_reset_password_for_user',
    description='Reset password for a user by admin'
)
class UserAdminPasswordResetView(BaseBloomerpDetailView, FormView):
    template_name = 'views/users/password_reset.html'
    form_class = AdminPasswordChangeForm
    model = User

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def has_permission(self):
        return self.request.user.is_superuser

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.get_object()
        return kwargs

    def form_valid(self, form: AdminPasswordChangeForm):
        self.object = self.get_object()
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        self.object = self.get_object()
        return super().form_invalid(form)
