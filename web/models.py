
from django.db import models
from django.utils.text import slugify

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Categorías"

class Tecnologia(models.Model):
    nombre = models.CharField(max_length=50)
    icono = models.CharField(max_length=50, help_text="Nombre de la clase de Font Awesome (ej: 'fa-python')")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Tecnologías"

class Proyecto(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    descripcion = models.TextField()
    imagen_principal = models.ImageField(upload_to='proyectos/')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='proyectos')
    tecnologias = models.ManyToManyField(Tecnologia, related_name='proyectos')
    url_github = models.URLField(blank=True, null=True)
    url_demo = models.URLField(blank=True, null=True)
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.titulo

class ImagenProyecto(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='proyectos/galeria/')
    titulo = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Imagen de {self.proyecto.titulo}"

class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.asunto} - {self.nombre}"

# 4. Admin para gestionar el contenido
# portfolio_app/admin.py