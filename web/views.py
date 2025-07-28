
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Proyecto, Categoria, Tecnologia,Contacto
from .forms import ContactoForm
from django.core.mail import EmailMultiAlternatives



def pagina_no_encontrada(request, exception):
    return render(request, '404.html', status=404)

class HomeView(ListView):
    model = Proyecto
    template_name = 'home.html'
    context_object_name = 'proyectos_destacados'
    
    def get_queryset(self):
        return Proyecto.objects.filter(destacado=True).order_by('-fecha_publicacion')[:3]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['tecnologias'] = Tecnologia.objects.all()
        return context

class ProyectoListView(ListView):
    model = Proyecto
    template_name = 'proyectos.html'
    context_object_name = 'proyectos'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Proyecto.objects.all().order_by('-fecha_publicacion')
        
        # Filtrar por categoría si se especifica
        categoria_slug = self.kwargs.get('categoria_slug')
        if categoria_slug:
            queryset = queryset.filter(categoria__slug=categoria_slug)
        
        # Filtrar por tecnología si se especifica
        tecnologia_id = self.request.GET.get('tecnologia')
        if tecnologia_id:
            queryset = queryset.filter(tecnologias__id=tecnologia_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['tecnologias'] = Tecnologia.objects.all()
        
        # Añadir la categoría actual al contexto
        categoria_slug = self.kwargs.get('categoria_slug')
        if categoria_slug:
            context['categoria_actual'] = get_object_or_404(Categoria, slug=categoria_slug)  
        return context

class ProyectoDetailView(DetailView):
    model = Proyecto
    template_name = 'proyecto_detalle.html'
    context_object_name = 'proyecto'
    slug_url_kwarg = 'proyecto_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Proyectos relacionados (misma categoría)
        proyecto_actual = self.get_object()
        context['proyectos_relacionados'] = Proyecto.objects.filter(
            categoria=proyecto_actual.categoria
        ).exclude(id=proyecto_actual.id)[:3]
        return context


class ContactoView(CreateView):
    model = Contacto
    form_class = ContactoForm
    template_name = 'contacto.html'
    
    def form_valid(self, form):
        # Guarda el objeto, pero sin usar super()
        form.save()

        # Extraer datos y enviar correo
        nombre = form.cleaned_data['nombre']
        correo = form.cleaned_data['email']
        asunto = form.cleaned_data['asunto']
        mensaje = form.cleaned_data['mensaje']

        # Composición del correo (como ya tienes)
        subject = f'Nuevo mensaje de contacto de {nombre}'
        from_email = correo
        to_email = ['donnyjpl@gmail.com']
        text_content = f'Nuevo mensaje de contacto de {nombre}\n\nCorreo: {correo}\n\nMensaje:\n{mensaje}'
        html_content = f"""
            <html>
                <body>
                    <h2>Nuevo mensaje de contacto de {nombre}</h2>
                    <p><strong>Asunto:</strong> {asunto}</p>
                    <p><strong>Correo:</strong> {correo}</p>
                    <p><strong>Mensaje:</strong></p>
                    <p>{mensaje}</p>
                </body>
            </html>
        """

        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        # Mensaje para el usuario
        messages.success(self.request, '¡Gracias por tu mensaje! Me pondré en contacto contigo pronto.')

        # Volver a renderizar el formulario limpio
        return self.render_to_response(self.get_context_data(form=ContactoForm()))

def about_view(request):
    return render(request, 'about.html')
