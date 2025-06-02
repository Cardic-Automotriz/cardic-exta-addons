# Módulo Odoo: hr_cardic

## Descripción

El módulo **hr_cardic** está diseñado para gestionar procesos clave de Recursos Humanos en Cardic Automotriz, principalmente la **solicitud y gestión de vacantes**. Permite a los usuarios registrar, aprobar y dar seguimiento a las solicitudes de nuevas vacantes dentro de la empresa, facilitando la comunicación entre los departamentos y la dirección.

## Funcionalidades principales

- **Registro de solicitudes de vacante:**  
  Los jefes de departamento pueden registrar solicitudes de nuevas vacantes, especificando detalles como descripción del puesto, nivel de estudios, horario, salario, etc.

- **Aprobación de solicitudes:**  
  La dirección puede revisar y aprobar o rechazar las solicitudes de vacantes.

- **Seguimiento de solicitudes:**  
  Se puede consultar el estado de cada solicitud (pendiente, aprobada, rechazada) y ver el historial de solicitudes.

- **Gestión de información relevante:**  
  El módulo almacena información clave para cada vacante, como jefe solicitante, nivel de estudios requerido, horario, salario y fecha de solicitud.

## Modelos principales

- `hr_cardic.solicitud`:  
  Modelo principal para el registro y gestión de solicitudes de vacantes.

## Vistas

- **Formulario de solicitud:**  
  Permite crear y editar solicitudes de vacante.
- **Lista de solicitudes:**  
  Muestra todas las solicitudes registradas y su estado.

## Menús

- **RRHH Cardic > Solicitudes > Lista de Solicitudes:**  
  Acceso rápido a la gestión de solicitudes de vacante.

## Instalación

1. Copia la carpeta `hr_cardic` en tu directorio de addons personalizados (`odoo-custom-addons`).
2. Actualiza la lista de aplicaciones en Odoo.
3. Instala el módulo desde el panel de aplicaciones.

## Uso

1. Ve al menú **RRHH Cardic > Solicitudes > Lista de Solicitudes**.
2. Haz clic en "Crear" para registrar una nueva solicitud de vacante.
3. Llena los campos requeridos y guarda la solicitud.
4. La dirección puede revisar y aprobar/rechazar la solicitud.
5. Da seguimiento al estado de cada solicitud desde la lista.

## Créditos

- **Autor:** Cardic Automotriz
- **Colaboradores:** Equipo de Recursos Humanos 