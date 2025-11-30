from django import forms
from django.contrib.auth.models import User


# --- small helper widget to mark password fields for the JS toggle ---
class PWInput(forms.PasswordInput):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.pop("attrs", {}) or {}
        # this attribute is what your JS looks for
        attrs.setdefault("data-toggle", "pw")
        super().__init__(attrs=attrs)


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            "required": "⚠️ Please enter your email address.",
            "invalid": "⚠️ Please enter a valid email address.",
        },
    )
    password1 = forms.CharField(
        widget=PWInput(),                       # <- instance + data-toggle="pw"
        label="Password",
        min_length=8,
        help_text="Password must be at least 8 characters long.",
        error_messages={"required": "⚠️ Please enter a password."},
    )
    password2 = forms.CharField(
        widget=PWInput(),                       # <- instance + data-toggle="pw"
        label="Confirm Password",
        error_messages={"required": "⚠️ Please confirm your password."},
    )

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("⚠️ This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("⚠️ This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("⚠️ Passwords do not match.")
        return cleaned_data
