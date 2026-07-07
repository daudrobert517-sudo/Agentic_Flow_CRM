from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

TEXT_INPUT_CLASSES = (
    'w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm text-gray-800 '
    'bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent '
    'placeholder-gray-300 transition-colors'
)


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'company_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': TEXT_INPUT_CLASSES})
            field.help_text = ''


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': TEXT_INPUT_CLASSES})