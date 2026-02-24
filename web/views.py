"""
Vistas del portafolio.

Principios SOLID aplicados:
- SRP: Las vistas solo manejan HTTP (entrada/salida). La lógica de negocio
       está delegada a los servicios en web/services/.
- DIP: Las vistas dependen de abstracciones (ContactEmailService, AIProvider),
       no de implementaciones concretas.
"""

import logging
import json

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Proyecto, Categoria, Tecnologia, Contacto
from .forms import ContactoForm
from .services.email_service import ContactEmailService
from .services.ai_service import GroqAIProvider

logger = logging.getLogger(__name__)

# ─── Instancias de servicios (inyección de dependencias) ──────────────────────
# Para cambiar el proveedor de email o IA, basta con cambiar estas líneas.
_email_service = ContactEmailService()
_ai_provider = GroqAIProvider()


# ─── Vistas de contenido ──────────────────────────────────────────────────────

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

        categoria_slug = self.kwargs.get('categoria_slug')
        if categoria_slug:
            queryset = queryset.filter(categoria__slug=categoria_slug)

        tecnologia_id = self.request.GET.get('tecnologia')
        if tecnologia_id:
            queryset = queryset.filter(tecnologias__id=tecnologia_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['tecnologias'] = Tecnologia.objects.all()

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
        proyecto = self.object  # Usa self.object en lugar de llamar get_object() dos veces
        context['proyectos_relacionados'] = (
            Proyecto.objects
            .filter(categoria=proyecto.categoria)
            .exclude(id=proyecto.id)[:3]
        )
        context['suggested_questions'] = [
            {'label': '💻 Tecnologías y su elección', 'question': '¿Qué tecnologías usaste en este proyecto y por qué las elegiste?'},
            {'label': '🎯 Desafíos técnicos', 'question': '¿Cuáles fueron los principales desafíos técnicos que enfrentaste en este proyecto?'},
            {'label': '📈 Escalabilidad', 'question': '¿Cómo escalabilizarías esta aplicación para manejar millones de usuarios?'},
            {'label': '⭐ Evaluación completa', 'question': 'Evalúa profesionalmente la arquitectura y las decisiones de diseño de este proyecto'},
            {'label': '🚀 Futuras mejoras', 'question': '¿Qué mejoras o nuevas funcionalidades se podrían implementar?'},
        ]
        return context


class ContactoView(CreateView):
    """
    Vista de contacto. Delega el envío de email a ContactEmailService (SRP / DIP).
    """
    model = Contacto
    form_class = ContactoForm
    template_name = 'contacto.html'

    def form_valid(self, form):
        form.save()

        exito = _email_service.send(
            nombre=form.cleaned_data['nombre'],
            correo=form.cleaned_data['email'],
            asunto=form.cleaned_data['asunto'],
            mensaje=form.cleaned_data['mensaje'],
        )

        if exito:
            messages.success(
                self.request,
                '¡Gracias por tu mensaje! Me pondré en contacto contigo pronto.'
            )
        else:
            messages.warning(
                self.request,
                'Tu mensaje fue guardado, pero hubo un problema al enviar la notificación.'
            )

        return self.render_to_response(self.get_context_data(form=ContactoForm()))


def about_view(request):
    suggested_questions = [
        {'label': '👤 ¿Quién es Donni Plaza?', 'question': 'Cuéntame sobre la trayectoria profesional y formación de Donni Plaza.'},
        {'label': '🛠️ Habilidades principales', 'question': '¿Cuáles son las habilidades técnicas y blandas más destacadas de Donni?'},
        {'label': '📂 Resumen de proyectos', 'question': '¿Qué tipo de proyectos ha desarrollado Donni y en qué áreas se especializa?'},
        {'label': '💡 ¿Por qué contratarlo?', 'question': '¿Cuál es el valor agregado que Donni aporta a un equipo o proyecto?'},
        {'label': '📞 Contacto', 'question': '¿Cómo puedo ponerme en contacto con Donni para una colaboración o empleo?'},
    ]
    return render(request, 'about.html', {'suggested_questions': suggested_questions})


# ─── API de Chat con IA ───────────────────────────────────────────────────────

@require_http_methods(["POST"])
def chat_general(request):
    """
    Endpoint para chatear con IA sobre el portafolio en general.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        portfolio_context = _build_general_context()
        ai_response = _ai_provider.get_response(user_message, portfolio_context, conversation_history)

        return JsonResponse({'response': ai_response, 'success': True})

    except Exception as e:
        logger.error(f"Error en chat_general: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)


@require_http_methods(["POST"])
def chat_proyecto(request, proyecto_slug):
    """
    Endpoint para chatear con IA sobre un proyecto específico.
    Delega la llamada a la IA a GroqAIProvider (SRP / DIP).
    """
    try:
        proyecto = Proyecto.objects.get(slug=proyecto_slug)

        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        if len(user_message) > 500:
            return JsonResponse({'error': 'Mensaje muy largo'}, status=400)

        project_context = _build_project_context(proyecto)
        ai_response = _ai_provider.get_response(user_message, project_context, conversation_history)

        return JsonResponse({'response': ai_response, 'success': True})

    except Proyecto.DoesNotExist:
        return JsonResponse({'error': 'Proyecto no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error en chat_proyecto: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)


def _build_project_context(proyecto: Proyecto) -> str:
    """Construye el texto de contexto del proyecto para la IA."""
    tecnologias = ", ".join([tech.nombre for tech in proyecto.tecnologias.all()])
    context = (
        f"Proyecto: {proyecto.titulo}\n"
        f"Categoría: {proyecto.categoria.nombre}\n"
        f"Descripción: {proyecto.descripcion}\n"
        f"Tecnologías utilizadas: {tecnologias}\n"
        f"Fecha de creación: {proyecto.fecha_creacion.strftime('%B %Y')}"
    )
    if proyecto.url_demo:
        context += f"\nDemo en vivo: {proyecto.url_demo}"
    if proyecto.url_github:
        context += f"\nRepositorio GitHub: {proyecto.url_github}"
    return context


def _build_general_context() -> str:
    """Construye el texto de contexto general del portafolio y del perfil del desarrollador."""
    proyectos = Proyecto.objects.all()
    proyectos_info = []
    for p in proyectos:
        techs = ", ".join([t.nombre for t in p.tecnologias.all()])
        proyectos_info.append(f"- {p.titulo} ({p.categoria.nombre}): {p.descripcion[:150]}... techs: {techs}")
    
    proyectos_summary = "\n".join(proyectos_info)
    
    context = (
        "PERFIL DEL DESARROLLADOR:\n"
        "Nombre: Donni Plaza\n"
        "Título: Ingeniero en Informática\n"
        "Experiencia: 5+ años como desarrollador independiente (freelance) y coordinador de tecnología.\n"
        "Especialidades: Desarrollo Full Stack (Python/Django, React), Bases de Datos, SEO, E-commerce.\n"
        "Ubicación: Santiago, Chile.\n"
        "Educación: Ingeniero en Informática (UPT Barlovento Argelia Laya), Bootcamp Full Stack Python (Talento Digital para Chile).\n\n"
        "PILA TECNOLÓGICA:\n"
        "- Lenguajes & Frameworks: Python (Django), JavaScript (React), HTML5, CSS3.\n"
        "- Bases de Datos: SQL, PostgreSQL.\n"
        "- Herramientas: Git, GitHub, AWS Cloud Practitioner.\n\n"
        "PROYECTOS EN EL PORTAFOLIO:\n"
        f"{proyectos_summary}\n\n"
        "LOGROS & CERTIFICACIONES:\n"
        "- AWS Cloud Practitioner (2025)\n"
        "- Bootcamp Full Stack Python (2024)\n"
        "- Diplomado Programación Web (2016)"
    )
    return context
