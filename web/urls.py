
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('proyectos/', views.ProyectoListView.as_view(), name='proyectos'),
    path('categorias/<slug:categoria_slug>/', views.ProyectoListView.as_view(), name='proyectos_por_categoria'),
    path('proyectos/<slug:proyecto_slug>/', views.ProyectoDetailView.as_view(), name='proyecto_detalle'),
    path('contacto/', views.ContactoView.as_view(), name='contacto'),
    path('contacto/exito/', views.contacto_exito, name='contacto_exito'),
    path('sobre-mi/', views.about_view, name='about'),
]
