# filepath: app/email.py
from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail # Asegúrate que mail esté disponible aquí (desde app/__init__.py)
from threading import Thread
from app.utils.negocio_actual import obtener_negocio

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Error al enviar email: {str(e)}")


def send_email(subject, recipients, text_body, html_body, sender=None):
    app = current_app._get_current_object()
    if sender is None:
        sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_appointment_confirmation_email(cliente_email, cliente_nombre, cita, token):
    # Asegúrate que 'public.confirmar_cita_route' sea el nombre de tu endpoint de confirmación
    confirm_url = url_for('public.confirmar_cita_route', token=token, _external=True)
    negocio = obtener_negocio()
    subject = f"Confirma tu cita en {negocio.nombre}"
    remitente = (negocio.remitente_nombre or negocio.nombre, current_app.config.get('MAIL_USERNAME'))

    # Para acceder a cita.servicio_rel.nombre y cita.barbero.nombre en la plantilla,
    # asegúrate que estas relaciones estén cargadas.
    # Si usas lazy='dynamic', necesitarías .all() o .first(), pero aquí son relaciones directas.
    # Si hay problemas, puedes pasar los nombres directamente:
    # servicio_nombre = cita.servicio_rel.nombre if cita.servicio_rel else "No especificado"
    # barbero_nombre = cita.barbero.nombre if cita.barbero else "No especificado"

    send_email(
        subject=subject,
        recipients=[cliente_email],
        sender=remitente,
        text_body=render_template('email/confirm_appointment.txt',
                                  cliente_nombre=cliente_nombre,
                                  cita=cita, # Pasas el objeto cita completo
                                  confirm_url=confirm_url,
                                  negocio=negocio),
        html_body=render_template('email/confirm_appointment.html',
                                  cliente_nombre=cliente_nombre,
                                  cita=cita, # Pasas el objeto cita completo
                                  confirm_url=confirm_url,
                                  negocio=negocio)
    )