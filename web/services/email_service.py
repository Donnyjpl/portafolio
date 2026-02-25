"""
Servicio de envío de emails de contacto.

Principios SOLID aplicados:
- SRP: Esta clase tiene una única responsabilidad — enviar el email de contacto.
- DIP: La vista depende de esta abstracción, no de EmailMultiAlternatives directamente.
- OCP: Para cambiar el proveedor de email (ej. SendGrid), se puede subclasificar
       sin tocar las vistas.
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape
from django.conf import settings

logger = logging.getLogger(__name__)


class ContactEmailService:
    """
    Encapsula la lógica de envío del email de contacto.

    Uso:
        service = ContactEmailService()
        service.send(nombre="Juan", correo="juan@mail.com",
                     asunto="Hola", mensaje="Me gustaría...")
    """

    def send(self, nombre: str, correo: str, asunto: str, mensaje: str) -> bool:
        """
        Envía el email de contacto al destinatario configurado en settings.

        Retorna True si el envío fue exitoso, False en caso contrario.
        """
        subject = f'Nuevo mensaje de contacto de {nombre}'
        to_email = [settings.CONTACT_EMAIL]

        text_content = (
            f'Nuevo mensaje de contacto de {nombre}\n\n'
            f'Asunto: {asunto}\n'
            f'Correo: {correo}\n\n'
            f'Mensaje:\n{mensaje}'
        )

        html_content = f"""
            <html>
                <body>
                    <h2>Nuevo mensaje de contacto de {escape(nombre)}</h2>
                    <p><strong>Asunto:</strong> {escape(asunto)}</p>
                    <p><strong>Correo:</strong> {escape(correo)}</p>
                    <p><strong>Mensaje:</strong></p>
                    <p>{escape(mensaje)}</p>
                </body>
            </html>
        """

        try:
            email = EmailMultiAlternatives(subject, text_content, correo, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Email de contacto enviado exitosamente desde {correo}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar email de contacto: {str(e)}", exc_info=True)
            return False
