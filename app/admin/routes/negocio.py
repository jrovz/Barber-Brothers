"""Configuración del negocio: contacto, ubicación, redes, SEO, historia, horario y datos legales."""
import re

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.admin import bp
from app.admin.forms import NegocioForm
from app.utils.decorators import admin_required
from app.utils.negocio_actual import obtener_negocio, limpiar_cache_negocio
from app.models.negocio import Negocio

DIAS = [
    ('Monday', 'Lunes'), ('Tuesday', 'Martes'), ('Wednesday', 'Miércoles'),
    ('Thursday', 'Jueves'), ('Friday', 'Viernes'), ('Saturday', 'Sábado'), ('Sunday', 'Domingo'),
]
_CLAVES_DIAS = [clave for clave, _ in DIAS]
_HORA = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
_CAMPOS_TEXTO = [
    'telefono', 'whatsapp', 'telefono_tienda', 'email_contacto', 'remitente_nombre',
    'direccion', 'ciudad', 'departamento', 'pais',
    'instagram_url', 'tiktok_url', 'facebook_url',
    'seo_titulo', 'seo_descripcion', 'seo_palabras_clave', 'historia',
    'razon_social', 'nit', 'direccion_legal', 'email_datos_personales',
]


def horario_por_dia(horario):
    """[{"dias": [...], "abre", "cierra"}] -> {"Monday": {"abre", "cierra"}, ...}"""
    por_dia = {}
    for tramo in horario or []:
        dias = tramo.get('dias') or []
        if isinstance(dias, str):
            dias = [dias]
        for dia in dias:
            por_dia[dia] = {'abre': tramo.get('abre', ''), 'cierra': tramo.get('cierra', '')}
    return por_dia


def horario_desde_dias(por_dia):
    """Agrupa días consecutivos con el mismo horario en un solo tramo."""
    tramos = []
    for clave in _CLAVES_DIAS:
        h = por_dia.get(clave)
        if not h:
            continue
        ultimo = tramos[-1] if tramos else None
        indice = _CLAVES_DIAS.index(clave)
        if (ultimo and ultimo['abre'] == h['abre'] and ultimo['cierra'] == h['cierra']
                and ultimo['dias'][-1] == _CLAVES_DIAS[indice - 1]):
            ultimo['dias'].append(clave)
        else:
            tramos.append({'dias': [clave], 'abre': h['abre'], 'cierra': h['cierra']})
    return tramos


def _leer_horario_del_formulario():
    """Devuelve (por_dia, errores). Un día sin horas queda cerrado."""
    por_dia, errores = {}, []
    for clave, nombre in DIAS:
        abre = (request.form.get(f'h_{clave}_abre') or '').strip()
        cierra = (request.form.get(f'h_{clave}_cierra') or '').strip()
        if not abre and not cierra:
            continue
        if not (_HORA.match(abre) and _HORA.match(cierra)):
            errores.append(f'{nombre}: usa el formato HH:MM en la apertura y el cierre.')
        elif abre >= cierra:
            errores.append(f'{nombre}: la hora de cierre debe ser posterior a la de apertura.')
        else:
            por_dia[clave] = {'abre': abre, 'cierra': cierra}
    return por_dia, errores


@bp.route('/negocio', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion_negocio():
    negocio_id = getattr(obtener_negocio(), 'id', None)
    negocio = db.session.get(Negocio, negocio_id) if negocio_id else None
    if negocio is None:
        flash('No se encontró el negocio configurado.', 'danger')
        return redirect(url_for('admin.dashboard'))

    form = NegocioForm(obj=negocio)
    por_dia = horario_por_dia(negocio.horario_atencion)

    if request.method == 'POST':
        por_dia, errores_horario = _leer_horario_del_formulario()
        for e in errores_horario:
            flash(e, 'danger')
        if form.validate() and not errores_horario:
            for campo in _CAMPOS_TEXTO:
                valor = getattr(form, campo).data
                setattr(negocio, campo, (valor.strip() or None) if isinstance(valor, str) else valor)
            negocio.pais = negocio.pais or 'Colombia'
            negocio.latitud = form.latitud.data
            negocio.longitud = form.longitud.data
            negocio.horario_atencion = horario_desde_dias(por_dia)
            db.session.commit()
            limpiar_cache_negocio()
            flash('Datos del negocio actualizados.', 'success')
            return redirect(url_for('admin.configuracion_negocio'))
        if form.errors:
            flash('Revisa los campos marcados en rojo.', 'danger')

    return render_template('admin/negocio.html', form=form, negocio=negocio, dias=DIAS,
                           horario=por_dia, title='Configuración del negocio')
