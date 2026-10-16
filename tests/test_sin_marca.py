"""Detecta marca escrita a mano fuera de la tabla `negocios` (fase 1).

Si falla, el mensaje lista archivo y línea de cada aparición.
"""
import ast
import io
import os
import tokenize

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARPETAS = [
    os.path.join(RAIZ, 'app', 'templates'),
    os.path.join(RAIZ, 'app', 'static', 'js'),
    os.path.join(RAIZ, 'app', 'public'),
    os.path.join(RAIZ, 'app', 'models'),
    os.path.join(RAIZ, 'app', 'utils'),
]

MARCAS = [
    'Barber Brothers',
    'barberbrothers',
    'la_barberbrothers',
    '3143782855',
    '314 378 2855',
    '3102160496',
    'Arkambuco',
    'Ibagué',
]


def _lineas_ignoradas_python(contenido):
    """Números de línea que son comentario o docstring: no los ve el cliente final."""
    ignoradas = set()

    try:
        for tok in tokenize.generate_tokens(io.StringIO(contenido).readline):
            if tok.type == tokenize.COMMENT:
                ignoradas.add(tok.start[0])
    except (tokenize.TokenizeError, SyntaxError, IndentationError):
        pass

    try:
        arbol = ast.parse(contenido)
    except SyntaxError:
        return ignoradas

    nodos = [arbol] + [
        n for n in ast.walk(arbol)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for nodo in nodos:
        primero = nodo.body[0] if nodo.body else None
        if (isinstance(primero, ast.Expr)
                and isinstance(primero.value, ast.Constant)
                and isinstance(primero.value.value, str)):
            inicio = primero.lineno
            fin = getattr(primero, 'end_lineno', inicio)
            ignoradas.update(range(inicio, fin + 1))

    return ignoradas


def _archivos_a_revisar():
    for carpeta in CARPETAS:
        if not os.path.isdir(carpeta):
            continue
        for dirpath, _, nombres in os.walk(carpeta):
            if '__pycache__' in dirpath:
                continue
            for nombre in nombres:
                if nombre.endswith('.md'):
                    continue
                yield os.path.join(dirpath, nombre)


def _apariciones(ruta):
    with open(ruta, encoding='utf-8') as f:
        contenido = f.read()

    ignoradas = _lineas_ignoradas_python(contenido) if ruta.endswith('.py') else set()

    encontradas = []
    for num, linea in enumerate(contenido.splitlines(), start=1):
        if num in ignoradas:
            continue
        for marca in MARCAS:
            if marca in linea:
                encontradas.append((ruta, num, marca))
    return encontradas


def test_sin_marca_escrita_a_mano():
    apariciones = []
    for ruta in _archivos_a_revisar():
        apariciones.extend(_apariciones(ruta))

    relativas = '\n'.join(
        f'{os.path.relpath(ruta, RAIZ)}:{num}: "{marca}"'
        for ruta, num, marca in apariciones
    )
    mensaje = f'{len(apariciones)} apariciones de marca escrita a mano:\n{relativas}'

    assert not apariciones, mensaje
