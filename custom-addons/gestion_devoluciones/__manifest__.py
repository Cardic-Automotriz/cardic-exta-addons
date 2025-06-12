# -*- coding: utf-8 -*-
{
    'name': 'Gestión de Devoluciones',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Gestión de devoluciones de producto con clasificación',
    'description': """
        Este módulo extiende la funcionalidad de Odoo para gestionar devoluciones de producto
        con un proceso de clasificación especializado.
    """,
    'author': 'Tu Nombre',
    'website': 'https://www.tuempresa.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'data/cron.xml',
        'views/stock_picking_views.xml',
        'views/menu_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}