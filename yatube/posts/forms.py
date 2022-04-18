from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': ('Текст'),
                  'group': ('Группа'),
                  'image': ('Изображение'),
                  }
        help_text = {
            'text': 'Поле для ввода текста поста',
            'group': 'Выберете соответствующую группу',
            'image': 'Добавить изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': ('Текст коментария'),
        }
        help_texts = {
            'text': ('Текст нового коментария'),
        }
