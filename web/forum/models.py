from django.db import models
from knowledge_base.models import QA
from django.forms import ModelForm
from django.forms import modelform_factory
from django.forms import Textarea

class Thread(models.Model):
    user_id =models.IntegerField(default=0)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return f'thread/{self.pk}/'

ThreadForm = modelform_factory(Thread, fields=["user_id", "question"])
Form = modelform_factory(Thread, form=ThreadForm, widgets={"question": Textarea()})

class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.DO_NOTHING)
    qa = models.ForeignKey(QA, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return f'/post/{self.pk}/'

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["qa"]