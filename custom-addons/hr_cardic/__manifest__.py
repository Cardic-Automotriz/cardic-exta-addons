{
    'name': 'Solicitud de Vacante y Gestión de Rutas',
    'summary': 'Gestión de solicitudes de vacantes RRHH Cardic y control de rutas',
    'description': 'Módulo para gestionar solicitudes de vacantes, rutas y cajas chicas en RRHH.',
    'author': 'Cardic Automotriz',
    'website': 'https://www.cardic.com',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_expense',
        'hr_recruitment',
        'hr_contract',
        'hr_attendance',
        'hr_holidays',
        'project',
        'account',
        'analytic'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
}