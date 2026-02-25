"""
Servicio de integración con IA para el chat de proyectos.

Principios SOLID aplicados:
- SRP: Cada clase tiene una única responsabilidad.
- OCP: Para agregar un nuevo proveedor (OpenAI, Anthropic...) basta con crear
       una nueva subclase de AIProvider sin modificar el código existente.
- LSP: GroqAIProvider es intercambiable con cualquier otra implementación de AIProvider.
- DIP: La vista depende de la abstracción AIProvider, no de la implementación concreta.
"""

import logging
import requests
from abc import ABC, abstractmethod
from decouple import config

logger = logging.getLogger(__name__)

# ─── Abstracción (interfaz) ────────────────────────────────────────────────────

class AIProvider(ABC):
    """
    Contrato que deben cumplir todos los proveedores de IA.
    Para agregar un nuevo proveedor, subclasifica esta clase e implementa get_response().
    """

    @abstractmethod
    def get_response(self, user_message: str, project_context: str, history: list) -> str:
        """
        Obtiene una respuesta de la IA dado un mensaje, contexto del proyecto e historial.

        Args:
            user_message: El mensaje del usuario.
            project_context: Información del proyecto como contexto para la IA.
            history: Lista de mensajes anteriores [{"role": ..., "content": ...}].

        Returns:
            La respuesta de la IA como string.
        """
        ...


# ─── Implementación concreta: Groq ────────────────────────────────────────────

class GroqAIProvider(AIProvider):
    """
    Implementación de AIProvider usando la API de Groq (llama-3.3-70b-versatile).

    Para cambiar de proveedor, crea otra subclase de AIProvider (ej. OpenAIProvider)
    y úsala en la vista sin tocar ningún otro código.
    """

    GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
    MODEL = 'llama-3.3-70b-versatile'
    MAX_HISTORY_MESSAGES = 6
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    TIMEOUT_SECONDS = 30

    SYSTEM_PROMPT_TEMPLATE = """Eres un asistente técnico experto que ayuda a evaluar y explicar proyectos de desarrollo de software.

CONTEXTO DEL PROYECTO:
{project_context}

TU MISIÓN:
1. Responder preguntas sobre este proyecto de manera técnica y profesional
2. Evaluar aspectos técnicos cuando te lo soliciten (arquitectura, tecnologías, escalabilidad)
3. Proporcionar feedback constructivo y destacar las fortalezas
4. Explicar decisiones técnicas de forma clara
5. Ser conciso pero completo (máximo 3-4 párrafos por respuesta)
6. Mostrar entusiasmo profesional por el proyecto

ESTILO:
- Responde en español
- Sé amigable pero profesional
- Usa términos técnicos apropiados
- Da ejemplos concretos cuando sea útil
- Si no tienes información específica, sé honesto y da respuestas generales"""

    def __init__(self):
        self._api_key = config('GROQ_API_KEY', default='')

    def get_response(self, user_message: str, project_context: str, history: list) -> str:
        if not self._api_key:
            logger.error("GROQ_API_KEY no está configurada en el entorno.")
            return "❌ La IA no está configurada correctamente. Contacta al administrador."

        messages = self._build_messages(user_message, project_context, history)

        try:
            response = requests.post(
                self.GROQ_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self._api_key}',
                },
                json={
                    'model': self.MODEL,
                    'messages': messages,
                    'temperature': self.TEMPERATURE,
                    'max_tokens': self.MAX_TOKENS,
                    'top_p': 1,
                    'stream': False,
                },
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except requests.exceptions.Timeout:
            return "⏱️ La solicitud tardó mucho tiempo. Por favor intenta nuevamente."
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la API de Groq: {str(e)}", exc_info=True)
            return "❌ Hubo un error al conectar con la IA. Por favor intenta en unos momentos."
        except Exception as e:
            logger.error(f"Error inesperado en GroqAIProvider: {str(e)}", exc_info=True)
            return "❌ Error inesperado. Por favor intenta nuevamente."

    def _build_messages(self, user_message: str, project_context: str, history: list) -> list:
        """Construye la lista de mensajes para la API."""
        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT_TEMPLATE.format(
                    project_context=project_context
                ),
            }
        ]
        # Limitar historial para no exceder tokens
        for msg in history[-self.MAX_HISTORY_MESSAGES:]:
            messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_message})
        return messages
