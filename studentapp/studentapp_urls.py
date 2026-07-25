from django.urls import path
from .views import *

urlpatterns = [

    path('profile/', StudentProfile.as_view()),

    path('student/tuitions/', StudentTuitionFeed.as_view()),
    path('student/tasks/', StudentTaskList.as_view()),
    path('student/task/<int:id>/', StudentTaskDetail.as_view()),
    path('student/task/<int:id>/submit/', SubmitTask.as_view()),

    path('community/request/', RequestCommunity.as_view()),
    path('community/join/<int:community_id>/', JoinCommunity.as_view()),

    path('post/create/', CreatePost.as_view()),
    path('post/like/<int:post_id>/', LikePost.as_view()),
    

    path('feed/', StudentFeed.as_view()),
]