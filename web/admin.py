
from django.contrib import admin
from .models import Categoria, Tecnologia, Proyecto, ImagenProyecto, Contacto

class ImagenProyectoInline(admin.TabularInline):
    model = ImagenProyecto
    extra = 1

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'destacado', 'fecha_creacion')
    list_filter = ('categoria', 'destacado', 'tecnologias')
    search_fields = ('titulo', 'descripcion')
    prepopulated_fields = {'slug': ('titulo',)}
    inlines = [ImagenProyectoInline]

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Tecnologia)
class TecnologiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono')

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'nombre', 'email', 'fecha', 'leido')
    list_filter = ('leido', 'fecha')
    search_fields = ('nombre', 'email', 'asunto', 'mensaje')
