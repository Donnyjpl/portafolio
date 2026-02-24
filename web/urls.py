
from django.urls import path
from . import views
from django.conf.urls import handler404

handler404 = 'web.views.pagina_no_encontrada'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('proyectos/', views.ProyectoListView.as_view(), name='proyectos'),
    path('categorias/<slug:categoria_slug>/', views.ProyectoListView.as_view(), name='proyectos_por_categoria'),
    path('proyectos/<slug:proyecto_slug>/', views.ProyectoDetailView.as_view(), name='proyecto_detalle'),
    path('contacto/', views.ContactoView.as_view(), name='contacto'),
    path('sobre-mi/', views.about_view, name='about'),
    
    # NUEVA: URL para el chat con IA
    path('api/chat/general/', views.chat_general, name='chat_general'),
    path('api/chat/<slug:proyecto_slug>/', views.chat_proyecto, name='chat_proyecto'),
]


