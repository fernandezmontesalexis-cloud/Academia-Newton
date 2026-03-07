from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registrar_alumno/', views.registrar_alumno, name='registrar_alumno'),
    path('logout/', views.logout_view, name='logout'),
    path('matriculas/', views.matriculas, name='matricula'),
]