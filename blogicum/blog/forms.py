from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()

class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ['author']


class CommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': 5, 'cols': 40}
        )
    )

    class Meta:
        model = Comment
        exclude = ['author', 'post', 'created_at']


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
