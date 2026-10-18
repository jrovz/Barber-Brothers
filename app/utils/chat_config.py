from flask import current_app


def chat_activo(app=None):
    """True solo si el chat está activado Y hay clave de API.

    Con cualquiera de las dos cosas faltando, el chat no existe: el endpoint responde
    404 y el widget no se dibuja, de modo que el sitio queda igual que sin chatbot.
    """
    app = app or current_app
    return bool(app.config.get('CHAT_ENABLED') and app.config.get('ANTHROPIC_API_KEY'))
