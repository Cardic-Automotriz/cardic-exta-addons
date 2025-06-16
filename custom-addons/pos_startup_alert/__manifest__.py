# -*- coding: utf-8 -*-
{
    'name': "POS Console Log Button (Test)",
    'version': '17.0.4.0',  # Versión de depuración
    'summary': "Añade un botón de prueba al POS que escribe en la consola.",
    'description': """
        Para fines de depuración, este módulo añade un botón a la pantalla 
        de productos del POS. Al hacer clic, imprimirá un mensaje en la consola
        del navegador y mostrará un popup.
    """,
    'author': "Tu Nombre (para depuración)",
    'category': 'Sales/Point of Sale',
    'depends': [
        'point_of_sale'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_startup_alert/static/src/js/startup_alert.js',
            'pos_startup_alert/static/src/xml/custom_button.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}