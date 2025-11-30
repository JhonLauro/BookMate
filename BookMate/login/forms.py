from django import forms
from django.contrib.auth.forms import AuthenticationForm


# --- small helper widget to mark password fields for the JS toggle ---
class PWInput(forms.PasswordInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {}) or {}
        # this attribute is what your JS looks for
        attrs.setdefault("data-toggle", "pw")
        super().__init__(attrs=attrs)


class LoginForm(AuthenticationForm):
    # make sure the login password also gets the toggle
    password = forms.CharField(label="Password", strip=False, widget=PWInput())

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            raise forms.ValidationError("Invalid username or password. Please try again.")
        return cleaned_data
