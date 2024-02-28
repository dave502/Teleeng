from django.urls import path, include
from . import views
from rest_framework import routers, serializers, viewsets


# router = routers.DefaultRouter()
# router.register(r'qa', views.QAViewSet)

app_name = 'knowledge_base'
urlpatterns = [
    path("", views.QAListView.as_view(), name="list_qa"),
    path("get", views.process_get, name="get_qa"),
    path("post", views.process_post, name="post_qa"),
    path("<int:pk>", views.QADetailView.as_view(), name="item_qa"),
    path("add", views.QACreateView.as_view(), name="add_qa"),
    path("<int:pk>/edit/", views.QAUpdateView.as_view(), name="edit_qa"),
    path("<int:pk>/del/", views.QADeleteView.as_view(), name="del_qa"),
]
