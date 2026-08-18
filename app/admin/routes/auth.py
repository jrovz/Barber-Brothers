"""Autenticacion y sesion del panel de administrador."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import bp
from app.models.admin import User
from app.admin.forms import LoginForm

import logging

logger = logging.getLogger(__name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Acceso a la ruta de login de administrador")
    
    try:
        if current_user.is_authenticated:
            logger.info(f"Usuario ya autenticado: {current_user.username}")
            if hasattr(current_user, 'is_admin') and current_user.is_admin():
                logger.info(f"Usuario confirmado como admin: {current_user.username}")
                return redirect(url_for('admin.dashboard'))
            else:
                logger.warning(f"Usuario autenticado pero no es admin: {current_user.username}")
    except Exception as e:
        logger.error(f"Error al verificar usuario autenticado: {str(e)}", exc_info=True)

    form = LoginForm()
    if form.validate_on_submit():
        logger.info(f"Intento de inicio de sesión con usuario: {form.username.data}")
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                logger.warning(f"Usuario no encontrado: {form.username.data}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            logger.info(f"Usuario encontrado: {user.username}, rol: {user.role}")
            
            if not user.check_password(form.password.data):
                logger.warning(f"Contraseña incorrecta para usuario: {user.username}")
                flash('Usuario o contraseña inválidos.', 'danger')
                return redirect(url_for('admin.login'))
            
            if not hasattr(user, 'is_admin'):
                logger.error(f"El usuario {user.username} no tiene el atributo is_admin")
                flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
                return redirect(url_for('public.home'))
                
            if not user.is_admin():
                logger.warning(f"Usuario no es admin: {user.username}, rol: {user.role}")
                flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
                return redirect(url_for('public.home'))

            login_user(user, remember=form.remember_me.data)
            logger.info(f"Inicio de sesión exitoso para admin: {user.username}")
            flash('Inicio de sesión exitoso.', 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard')
            return redirect(next_page)
            
        except Exception as e:
            logger.error(f"Error durante el proceso de autenticación: {str(e)}", exc_info=True)
            flash('Ocurrió un error durante la autenticación. Por favor, inténtalo de nuevo.', 'danger')
            return redirect(url_for('admin.login'))
        
    return render_template('login.html', title='Iniciar Sesión Admin', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('public.home'))


