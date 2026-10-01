from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from PIL import Image, UnidentifiedImageError
from .models import Profile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=254)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError("An account with this email already exists.")
        return email

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("bio", "avatar")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3, "maxlength": 280})}
    def clean_avatar(self):
        image = self.cleaned_data.get("avatar")
        if image and image.size > 5 * 1024 * 1024: raise forms.ValidationError("Image files must be 5 MB or smaller.")
        if image:
            try:
                image.seek(0)
                with Image.open(image) as uploaded:
                    if uploaded.format not in {"JPEG", "PNG", "WEBP"} or uploaded.width * uploaded.height > 25_000_000:
                        raise forms.ValidationError("Upload a JPEG, PNG, or WebP image smaller than 25 megapixels.")
                    uploaded.verify()
                image.seek(0)
            except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
                raise forms.ValidationError("The uploaded file is not a valid image.")
        return image
