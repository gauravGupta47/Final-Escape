from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create_story/', views.create_story, name='create_story'),
    path('continue_story/<int:story_id>/', views.continue_story, name='continue_story'),
    path('story_complete/<int:story_id>/', views.story_complete, name='story_complete'),
    path('check_image_status/<int:response_id>/', views.check_image_status, name='check_image_status'),
]
