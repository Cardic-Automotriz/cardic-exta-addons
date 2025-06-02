{
    'name': 'Solicitud de Vacante',
    'summary': 'Gestión de solicitudes de vacantes RRHH Cardic',
    'description': 'Módulo para gestionar solicitudes de vacantes y su flujo en RRHH.',
    'author': 'Cardic Automotriz',
    'website': 'https://www.cardic.com',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
} 