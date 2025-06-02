from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-story/', views.create_story, name='create_story'),
    path('continue-story/<int:story_id>/', views.continue_story, name='continue_story'),
    path('story-complete/<int:story_id>/', views.story_complete, name='story_complete'),
]
