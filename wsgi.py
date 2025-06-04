from app import create_app
import os

# Crear la aplicación para producción
app = create_app('production')

if __name__ == '__main__':
    # Solo para desarrollo local
    app.run(debug=False, host='0.0.0.0', port=5000)