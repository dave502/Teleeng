from django.urls import path

from . import views

app_name = 'forum'
urlpatterns = [
    path("", views.ThreadListView.as_view(), name="threads"),
    path("thread/<int:pk>/", views.ThreadDetailView.as_view(), name="thread"),
    path("post/<int:id>/", views.CreatePostView.as_view(), name="createpost"),
]
