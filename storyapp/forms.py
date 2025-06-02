from django import forms
from .models import User, Story, StoryResponse


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email'}),
        }


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['theme', 'character_name']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'character_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Character name'}),
        }


class StoryResponseForm(forms.ModelForm):
    class Meta:
        model = StoryResponse
        fields = ['user_input']
        widgets = {
            'user_input': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'What happens next?', 'rows': 3}),
        }
