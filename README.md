# Módulos Personalizados Odoo - Cardic Automotriz

Este directorio contiene los módulos personalizados desarrollados para Cardic Automotriz en Odoo.

## Estructura de Directorios

```
odoo-custom-addons/
├── profile_work/           # Módulo de gestión de vacantes RRHH
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── security/
│   │   └── ir.model.access.csv
│   └── views/
│       └── views.xml
└── README.md
```

## Módulos Disponibles

### profile_work
Módulo para la gestión de vacantes de recursos humanos.

#### Características
- Registro y seguimiento de vacantes
- Gestión de requisitos y perfiles
- Integración con el módulo de RRHH
- Campos personalizados para necesidades específicas de Cardic

#### Campos Principales
- Nombre de la vacante
- Descripción
- Nivel de estudios requerido
- Horario
- Salario propuesto
- Jefe solicitante
- Fecha de solicitud

## Desarrollo

### Requisitos
- Odoo 16.0 o superior
- Python 3.8+
- Acceso al servidor de desarrollo

### Configuración del Entorno

1. Asegúrate de que el directorio esté en la ruta correcta:
   ```bash
   /opt/odoo/odoo-custom-addons/
   ```

2. Verifica que el directorio esté incluido en la configuración de Odoo:
   ```bash
   # En el archivo de configuración de Odoo (odoo.conf)
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/odoo-custom-addons
   ```

### Instalación de Módulos

1. Reinicia el servidor Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

2. Actualiza la lista de aplicaciones:
   - Accede al backend de Odoo
   - Activa el "Modo desarrollador"
   - Ve a Aplicaciones
   - Haz clic en "Actualizar lista de aplicaciones"

3. Busca e instala los módulos necesarios

## Guía de Desarrollo

### Crear un Nuevo Módulo

1. Crea la estructura básica del módulo (usando el usuario odoo):
   ```bash
   sudo -u odoo mkdir nuevo_modulo
   cd nuevo_modulo
   sudo -u odoo mkdir models security views static
   sudo -u odoo touch __init__.py __manifest__.py
   sudo -u odoo touch models/__init__.py
   sudo -u odoo touch security/ir.model.access.csv
   sudo -u odoo touch views/views.xml
   ```

2. Configura el `__manifest__.py`:
   ```python
   {
       "name": "Nombre del Módulo",
       "summary": "Resumen corto",
       "description": "Descripción detallada",
       "author": "Cardic Automotriz",
       "category": "Categoría",
       "version": "1.0",
       "depends": ["base"],
       "data": [
           "security/ir.model.access.csv",
           "views/views.xml",
       ],
       "installable": True,
       "application": True,
   }
   ```

### Buenas Prácticas

1. **Control de Versiones**
   - Usa Git para el control de versiones
   - Crea ramas para nuevas características
   - Documenta los cambios en los commits

2. **Código**
   - Sigue las convenciones de Python (PEP 8)
   - Documenta las funciones y clases
   - Mantén el código modular y reutilizable

3. **Seguridad**
   - Define permisos de acceso apropiados
   - No expongas datos sensibles
   - Valida las entradas de usuario

4. **Testing**
   - Prueba en ambiente de desarrollo
   - Verifica la compatibilidad con otras versiones
   - Documenta los casos de prueba

## Mantenimiento

### Actualizaciones
- Mantén los módulos actualizados con la versión de Odoo
- Revisa regularmente las dependencias
- Haz backup antes de actualizar

### Backup
- Realiza backups regulares de la base de datos
- Mantén copias de seguridad del código
- Documenta los procedimientos de recuperación

## Soporte

Para soporte técnico o consultas sobre los módulos:
- Contacta al equipo de desarrollo de Cardic
- Reporta problemas en el sistema de tickets
- Consulta la documentación interna

## Licencia

Estos módulos son propiedad de Cardic Automotriz y su uso está restringido a la empresa.

---

Última actualización: 2024-03-19
Versión: 1.0
