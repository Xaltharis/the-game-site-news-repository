from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Введите ваш комментарий...',
                'class': 'comment-textarea'
            }),
            'parent': forms.HiddenInput(attrs={
                'class': 'parent-input'
            })
        }
        labels = {
            'content': ''
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False