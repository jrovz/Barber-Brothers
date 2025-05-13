from decimal import Decimal
import locale

def format_cop(value):
    """
    Formatea un valor numérico como moneda COP (Peso Colombiano).
    Ejemplo: 50000 -> COP 50.000
    """
    if value is None:
        return "N/A" # O puedes retornar un string vacío o "COP 0"
    try:
        # Asegurarse de que es un Decimal para el formateo
        val = Decimal(value)
        
        # Intentar usar la configuración regional para el formato de miles
        # Esto es opcional y depende de si 'es_CO' está disponible en el sistema
        try:
            locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
            # Formato con separador de miles y sin decimales para COP
            formatted_price = locale.format_string("%.0f", val, grouping=True)
        except locale.Error:
            # Fallback si la configuración regional no está disponible o falla
            # Formato manual simple
            formatted_price = f"{val:,.0f}".replace(",", ".")

        return f"COP {formatted_price}"
    except (TypeError, ValueError, locale.Error) as e:
        # En caso de cualquier error de conversión o formateo, retornar el valor original
        print(f"Error al formatear valor {value} como COP: {e}")
        return str(value)