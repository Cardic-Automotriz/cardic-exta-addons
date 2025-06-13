
# 📦 Módulos Personalizados Odoo – Cardic Automotriz

![Odoo Version](https://img.shields.io/badge/Odoo-17.0+-brightgreen)  
![Python Version](https://img.shields.io/badge/Python-3.10.12+-blue)  
![License](https://img.shields.io/badge/Licencia-Privada-red)  
![Status](https://img.shields.io/badge/Estado-En%20producción-success)

Este repositorio contiene los módulos personalizados desarrollados para **Cardic Automotriz** sobre la plataforma **Odoo**.

---

## 📁 Estructura de Directorios

```text
odoo-custom-addons/
├── hr_cardic/           # Gestión de vacantes de RRHH
├── stock_cardic/        # Rutas personalizadas de almacén y devoluciones
├── ml_connector/        # Conector con Mercado Libre México
├── odoo.conf            # Configuración de Odoo base
├── test/
├── docker-compose.yml
└── README.md
```

---

## 📦 Módulos Disponibles

| Módulo        | Descripción |
|---------------|-------------|
| `hr_cardic`   | Gestión de vacantes del área de Recursos Humanos. |
| `stock_cardic`| Gestión de rutas personalizadas de almacén, multiempresa, devoluciones y sincronización con plataformas externas. |
| `ml_connector`| Conexión con la API de Mercado Libre México para la sincronización y actualización masiva de publicaciones. Soporta más de **2.6M publicaciones** en 5 tiendas. |

---

## ⚙️ Requisitos de Desarrollo

- 🐍 Python `3.10.12+`
- 🧩 Odoo `17.0+`
- 📦 Docker
- ☁️ Acceso al entorno AWS o servidor de desarrollo Odoo

---

## 🏗️ Configuración del Entorno

<details>
<summary><strong>📦 Configuración del entorno en AWS</strong></summary>

1. Asegúrate de que el directorio esté en la ruta correcta:

   ```bash
   /opt/odoo/odoo-custom-addons/
   ```

2. Verifica que esté incluido en el archivo `odoo.conf`:

   ```ini
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/odoo-custom-addons
   ```

</details>

---

## 🚀 Instalación de Módulos

```bash
sudo systemctl restart odoo
```

Luego:
1. Accede al backend de Odoo  
2. Activa el **Modo Desarrollador**  
3. Ve a **Aplicaciones**  
4. Haz clic en **Actualizar Lista de Aplicaciones**  
5. Instala el módulo deseado

---

## 🛠️ Guía de Desarrollo

<details>
<summary><strong>➕ Crear un nuevo módulo</strong></summary>

```bash
sudo -u odoo mkdir nuevo_modulo
cd nuevo_modulo
sudo -u odoo mkdir models security views static
sudo -u odoo touch __init__.py __manifest__.py
sudo -u odoo touch models/__init__.py
sudo -u odoo touch security/ir.model.access.csv
sudo -u odoo touch views/views.xml
```

**Ejemplo de `__manifest__.py`:**

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

</details>

---

## 🐳 Ejecución en Contenedores Docker

<details>
<summary><strong>💡 Opción 1: Base de datos por defecto</strong></summary>

Agrega al `docker-compose.yml`:

```yaml
command: -- --init base --database odoo --without-demo all
```

</details>

<details>
<summary><strong>💼 Opción 2: Base de datos personalizada</strong></summary>

1. Inicializa la base con el comando anterior  
2. Accede a **Gestión de Bases de Datos**  
3. Crea tu base, configura el usuario admin y selecciona si deseas datos demo

</details>

---

## ✅ Buenas Prácticas

| Categoría | Recomendaciones |
|----------|-----------------|
| **Control de versiones** | Usa `git`, ramas por feature, mensajes de commit claros |
| **Código** | Sigue PEP8, documenta, mantén el código limpio y reutilizable |
| **Seguridad** | Define permisos, valida entradas, evita datos sensibles |
| **Pruebas** | Test en desarrollo, compatibilidad entre versiones, documenta casos de prueba |

---

## 🔄 Mantenimiento

| Área | Tareas |
|------|--------|
| **Actualizaciones** | Mantener compatibilidad con Odoo, revisar dependencias, realizar backups |
| **Backups** | Respaldo de base de datos y del código fuente, con procedimientos documentados |

---

## 🆘 Soporte

Para soporte o reportes:

- 📧 Contacta al equipo de desarrollo de **Cardic Automotriz**
- 🪪 Usa el sistema interno de tickets
- 📚 Consulta la documentación interna para dudas comunes

---

## 📜 Licencia

> Estos módulos son propiedad intelectual de **Cardic Automotriz**.  
> Su uso está **restringido exclusivamente** a personal autorizado de la empresa.

---

📅 **Última actualización:** `2024-03-19`  
🔢 **Versión:** `1.0`
