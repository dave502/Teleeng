from django.contrib import admin, messages
from .models import *

@admin.register(QA)
class QAAdmin(admin.ModelAdmin):
    list_display = "question", "answer", "updated_at"
    ordering = "updated_at",
    search_fields = "question",
    #list_filter = [StatusListFilter,  ("document", admin.RelatedOnlyFieldListFilter),]

    def question_short(self, obj: QA) -> str|None:
        return f"{obj.question[:20]  + '...?' if len(obj.question)>19 else ''}"

    def answer_short(self, obj: QA) -> str|None:
        return f"{obj.answer[:20]  + '...?' if len(obj.answer)>19 else ''}"