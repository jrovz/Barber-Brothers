from datetime import datetime

from app import db


class ChatMensaje(db.Model):
    """Un mensaje de una conversación del chatbot (del visitante o del asistente).

    Solo se guarda el texto visible de la conversación. La sesión es anónima: se
    identifica con un valor aleatorio en una cookie, nunca con datos del cliente.
    """
    __tablename__ = 'chat_mensajes'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    rol = db.Column(db.String(10), nullable=False)  # 'user' o 'assistant'
    contenido = db.Column(db.Text, nullable=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.CheckConstraint("rol IN ('user', 'assistant')", name='ck_chat_mensaje_rol'),
    )

    def __repr__(self):
        return f'<ChatMensaje {self.session_id[:8]} {self.rol}>'
