from typing import Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework import generics, permissions #https://www.django-rest-framework.org/#installation
from rest_framework.parsers import JSONParser
from knowledge_base.models import QA
from rest_framework import routers, serializers, viewsets
#from django.views.decorators.csrf import csrf_exempt

# Create your views here.


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def process_get(request: HttpRequest) -> HttpResponse:

    if request.method == 'GET':

        #q=request.GET.get("question", "")

        context = {

        }

    return render(request, "knowledge_base/request.html", context=context)


def process_post(request: HttpRequest) -> JsonResponse:

    if request.method == 'POST':

        try:
            data = JSONParser().parse(request)  # data is a dict
            qa = QA.objects.create(question=data["question"], answer=data["answer"])
            qa.save()
            return JsonResponse({}, status=201)
        except Exception as err:
            return JsonResponse({'error': err}, status=500)

    # return render(request, "knowledge_base/request.html", context=context)


class QASerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QA
        fields = ['question', 'answer']

class QAViewSet(viewsets.ModelViewSet):
    queryset = QA.objects.all()
    serializer_class = QASerializer

class QAView(View):
    def get(self, request):
        ...

class QAListView(ListView):
    #template_name=

    model = QA
    #context_object_name=
    # queryset  = (
    #     QA.objects.select_related("  ").prefetch_related(" ")
    # )

class QADetailView(DetailView):
    #template_name=

    model = QA
    #context_object_name=

class QACreateView(CreateView):
    #template_name=

    model = QA
    fields = "question", "answer"
    success_url = reverse_lazy("knowledge_base:list_qa")
    #form_class =

class QAUpdateView(UpdateView):
    template_name_suffix = "_update"

    model = QA
    fields = "question", "answer"
    success_url = reverse_lazy("knowledge_base:list_qa")
    #form_class =

class QADeleteView(DeleteView):
    model = QA
    success_url = reverse_lazy("knowledge_base:list_qa")
    #form_class =