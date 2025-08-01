from django.urls import path
from .views import (
    index, capa, 
   
    CalendarioView, dashboard_view, global_search_view
)

app_name = 'core'

urlpatterns = [
    path('home', index, name='index'),
    path('', capa, name='capa'),
    path('dashboard/', dashboard_view, name='dashboard'),
    # Removidas as URLs relacionadas a profiles
    # path('profiles/', profile_list, name='profile_list'),
    # path('profiles/<int:pk>/', profile_detail, name='profile_detail'),
    # path('profiles/create/', profile_create, name='profile_create'),
    # path('profiles/<int:pk>/update/', profile_update, name='profile_update'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('search/', global_search_view, name='global_search'),
]
