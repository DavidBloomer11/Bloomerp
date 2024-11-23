from django import forms

# ---------------------------------
# User Detail View Preference Form
# ---------------------------------
from bloomerp.models import UserDetailViewPreference

class UserDetailViewPreferenceForm(forms.Form):
    field = forms.CharField(max_length=100, required=False)
    id = forms.IntegerField(required=False)
    position = forms.ChoiceField(required=False, choices=UserDetailViewPreference.POSITION_CHOICES, initial=UserDetailViewPreference.POSITION_CHOICES[0][0])
    is_used = forms.BooleanField(required=False)

class UserDetailViewPreferenceFormset(forms.BaseFormSet):
    user = None
    def save(self, *args, **kwargs):
        for form in self.forms:
            form: UserDetailViewPreferenceForm
            if form.cleaned_data.get('id'):
                # Extract relevant data from the form
                id = form.cleaned_data.get('id',None)
                is_used = form.cleaned_data.get('is_used',False)
                position = form.cleaned_data.get('position',False)

                # Check if UserListViewPreference with specified conditions exists
                existing_preference = UserDetailViewPreference.objects.filter(
                    user=self.user,
                    application_field_id=id,
                ).first()

                # Implement your business logic here
                if existing_preference:
                    # UserListViewPreference with given conditions exists
                    if not is_used:
                        # If is_used is False, delete the existing preference
                        existing_preference.delete()
                    # Note: If is_used is True, no further action is required as we want to create it if it doesn't exist
                else:
                    # UserListViewPreference with given conditions does not exist
                    if is_used:
                        
                        # If is_used is True, create a new preference
                        UserDetailViewPreference.objects.create(
                            user=self.user,
                            application_field_id=id,
                            position=position
                        )


# ---------------------------------
# User selection form
# ---------------------------------
from bloomerp.models import User
class UserSelectionForm(forms.Form):
    users = forms.ModelChoiceField(
        queryset=User.objects.all(),
        empty_label="Select a user",  # Optional: Display a default label
        required=False
    )


# ---------------------------------
# User Creation Form
# ---------------------------------
from django.contrib.auth.forms import UserCreationForm
class BloomerpUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

