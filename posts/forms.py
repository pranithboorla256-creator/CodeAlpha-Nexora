from django import forms
from .models import Comment, Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("content",)
        widgets = {"content": forms.Textarea(attrs={"rows": 4, "maxlength": 1000, "placeholder": "What’s on your mind?"})}
    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content: raise forms.ValidationError("A post cannot be empty.")
        return content

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {"content": forms.TextInput(attrs={"maxlength": 500, "placeholder": "Write a comment…"})}
    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content: raise forms.ValidationError("A comment cannot be empty.")
        return content
