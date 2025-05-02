from django.urls import path
from .views import (
    index, capa, dashboard, 
    profile_list, profile_detail, 
    profile_create, profile_update,
    CalendarioView, dashboard_view,
)

app_name = 'core'

urlpatterns = [
    path('home', index, name='index'),
    path('', capa, name='capa'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profiles/', profile_list, name='profile_list'),
    path('profiles/<int:pk>/', profile_detail, name='profile_detail'),
    path('profiles/create/', profile_create, name='profile_create'),
    path('profiles/<int:pk>/update/', profile_update, name='profile_update'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
]