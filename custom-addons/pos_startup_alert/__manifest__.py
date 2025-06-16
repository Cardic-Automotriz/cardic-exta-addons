# -*- coding: utf-8 -*-
{
    'name': "POS Alerta de Inicio",
    'version': '17.0.1.1',  # He incrementado la versión para asegurar el cambio
    'summary': "Muestra una alerta al iniciar el Punto de Venta.",
    'description': """
        Este módulo muestra un popup de advertencia simple al momento de
        que un usuario inicia una nueva sesión en el Punto de Venta (POS).
        Diseñado para Odoo 17.
    """,
    'author': "Tu Nombre (para nuevo módulo)",
    'category': 'Sales/Point of Sale',
    'depends': [
        'point_of_sale'
    ],
    'assets': {
        'point_of_sale.assents': [
            'pos_startup_alert/static/src/js/startup_alert.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
