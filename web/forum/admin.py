from django.contrib import admin, messages
from .models import *
from django.utils.safestring import mark_safe
from django.urls import reverse


class Posts(admin.TabularInline):
    model = Post
    max_num = 1


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = "user_id", "question", "qa_link"
    readonly_fields = ('qa_link',)

    #ordering = "updated_at",
    search_fields = "question",

    inlines = [
        Posts,
    ]

    def qa_link(self, obj: QA) -> str|None:
        return mark_safe('<a href="{}">{}</a>'.format(
            f"/admin/knowledge_base/qa/{obj.post_set.all()[0].pk}/change/",
            obj.post_set.all()[0].qa
        ))

    qa_link.short_description = 'qa'
