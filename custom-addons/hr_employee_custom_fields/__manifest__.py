{
    'name': 'HR Employee Custom Fields',
    'summary': 'Calculo de nomina directamente en  el modulo de employes',
    'description': 'Se agregarin campso como ele claculo devaaiones, SDI, etc.',
    'author': 'Cardic Automotriz',
    'category': 'Human Resources',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'l10n_mx',
        'l10n_mx_hr',        
    ],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
} 