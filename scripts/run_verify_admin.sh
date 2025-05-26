#!/bin/bash
# Ejecutar script para verificar usuario administrador

# Verificar que las credenciales de GCP están configuradas
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
  echo "ADVERTENCIA: La variable GOOGLE_APPLICATION_CREDENTIALS no está configurada."
  echo "Es posible que necesite configurar las credenciales de GCP para acceder a Cloud SQL."
  echo ""
fi

# Obtener credenciales de base de datos si no están configuradas
if [ -z "${DB_USER}" ] || [ -z "${DB_PASS}" ]; then
  echo "Ingrese las credenciales de la base de datos:"
  
  # Solicitar DB_USER si no está configurado
  if [ -z "${DB_USER}" ]; then
    read -p "Usuario de base de datos: " DB_USER
    export DB_USER
  fi
  
  # Solicitar DB_PASS si no está configurado
  if [ -z "${DB_PASS}" ]; then
    read -s -p "Contraseña de base de datos: " DB_PASS
    echo ""
    export DB_PASS
  fi
fi

# Ejecutar el script de Python para verificar usuarios administradores
echo "Ejecutando verificación de usuarios administradores..."
echo "----------------------------------------------------"
python "$(dirname "$0")/verify_admin_gcp.py" --all-admins

# Verificar si se proporcionó un nombre de usuario específico
if [ $# -gt 0 ]; then
  echo ""
  echo "Verificando usuario específico: $1"
  echo "----------------------------------------------------"
  python "$(dirname "$0")/verify_admin_gcp.py" "$1"
fi

echo ""
echo "Verificación completada."
