from django.db import models
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver

class QA(models.Model):
    question = models.TextField(blank=False)
    answer = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    __original_answer = None

    def __init__(self, *args, **kwargs):
        super(QA, self).__init__(*args, **kwargs)
        self.__original_answer = self.answer

    # @property
    # def url_short(self) -> str:
    #     if len(self.url) < 50:
    #         return self.url
    #     return self.url[:50] + "..."

    class Meta:
        #managed = False
        verbose_name_plural = "QuestionsAnswers"
        db_table = 'qa'

    def __str__(self) -> str:
        return f"{self.question[:50]  + ('...?' if len(self.question)>49 else '')}" #: " \
              # f"{self.answer[:20]  + '...?' if len(self.answer)>19 else ''}"

    @staticmethod
    def post_save(sender, instance, created, **kwargs):
        if instance.previous_state != instance.state or created:
            print("SAVING")

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        __original_answer = None
        if self.answer != self.__original_answer:
            print("Ыф")
        # else:
        #     print("SAVING2")

        super(QA, self).save(force_insert, force_update, *args, **kwargs)
        self.__original_answer = self.answer
