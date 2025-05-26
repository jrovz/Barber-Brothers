"""
Script para habilitar la depuración de errores en Cloud Run

Este script muestra cómo configurar la aplicación Flask para 
mostrar información detallada de errores en Cloud Run.
"""

# 1. Modificar app/__init__.py para habilitar el modo de depuración

# Agregar en create_app() después de aplicar configuraciones:
"""
# Habilitar modo debug y mostrar errores detallados en Cloud Run
if os.environ.get('FLASK_DEBUG_GCP', 'False').lower() in ['true', '1', 't']:
    app.logger.info("Modo de depuración habilitado en GCP")
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True
"""

# 2. Agregar middleware para capturar y registrar errores

"""
@app.errorhandler(Exception)
def handle_exception(e):
    # Registrar el error detallado en Cloud Logging
    app.logger.error(f"Error no manejado: {str(e)}", exc_info=True)
    
    # En modo debug, mostrar error detallado
    if app.debug:
        return f"<pre>Error: {str(e)}\n\n{traceback.format_exc()}</pre>", 500
    else:
        # En producción, mostrar mensaje genérico
        return "Ocurrió un error interno del servidor. Los administradores han sido notificados.", 500
"""

# 3. Como habilitar errores detallados temporalmente en Cloud Run:
"""
# Configurar variable de entorno en Cloud Run
gcloud run services update barberia-app \
    --set-env-vars="FLASK_DEBUG_GCP=True" \
    --region=us-central1

# Para deshabilitar después:
gcloud run services update barberia-app \
    --set-env-vars="FLASK_DEBUG_GCP=False" \
    --region=us-central1
"""

# 4. Cómo revisar los registros de errores en Cloud Logging:
"""
# Obtener registros de errores
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND severity>=ERROR" --limit=20
"""

# 5. Instrucciones para habilitar depuración específica en autenticación
"""
# Agregar en app/admin/routes.py en la función login():

@bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin():
            return redirect(url_for('admin.dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            # Depuración: registrar intento de login
            current_app.logger.info(f"Intento de login para usuario: {form.username.data}")
            
            user = User.query.filter_by(username=form.username.data).first()
            
            # Depuración: información del usuario encontrado o no
            if user:
                current_app.logger.info(f"Usuario encontrado: {user.username}, rol: {user.role}")
            else:
                current_app.logger.warning(f"Usuario no encontrado: {form.username.data}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            # Verificar contraseña
            if not user.check_password(form.password.data):
                current_app.logger.warning(f"Contraseña inválida para usuario: {user.username}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            # Verificar rol
            if not hasattr(user, 'is_admin') or not user.is_admin():
                current_app.logger.warning(f"Usuario {user.username} no tiene permisos de administrador (rol: {user.role})")
                flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
                return redirect(url_for('public.home'))

            # Login exitoso
            login_user(user, remember=form.remember_me.data)
            current_app.logger.info(f"Login exitoso para usuario: {user.username}")
            flash('Inicio de sesión exitoso.', 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
    except Exception as e:
        # Capturar y registrar cualquier error
        current_app.logger.error(f"Error en login: {str(e)}", exc_info=True)
        flash('Ocurrió un error durante el inicio de sesión. Por favor, intenta nuevamente.', 'danger')
        return render_template('login.html', title='Iniciar Sesión Admin', form=form, error_details=str(e) if current_app.debug else None)
            
    return render_template('login.html', title='Iniciar Sesión Admin', form=form)
"""
