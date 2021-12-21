from django.utils.translation import ugettext_lazy as _
from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            "text": _("Текст поста"),
            "group": _("Название группы"),
            "image": _("Картинка поста")
        }

    def cleaned_data(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Заполните это поле')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            "text": _("Текст комментария"),
        }
