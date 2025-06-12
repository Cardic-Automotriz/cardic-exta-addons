# -*- coding: utf-8 -*-
{
    'name': "Gestión de Devoluciones Mejorada",
    'summary': """
        Mejora el proceso de devoluciones de clientes, añadiendo ubicaciones
        intermedias y razones de devolución.""",
    'description': """
        Este módulo personaliza el flujo de trabajo de las devoluciones en Odoo.
        - Crea una ubicación de "Devoluciones" para recibir productos devueltos.
        - Crea una ubicación de "Garantía / Revisión".
        - Permite al usuario decidir si el producto vuelve al stock o va a garantía.
        - Añade un campo para especificar el motivo de la devolución.
    """,
    'author': "Tu Nombre o Empresa",
    'website': "https://www.tuweb.com",
    'category': 'Inventory/Inventory',
    'version': '1.0',

    # ¡LA LÍNEA MÁS IMPORTANTE!
    # Aquí declaramos que nuestro módulo depende de 'stock'.
    'depends': ['stock'],

    # Los archivos de datos y vistas que carga el módulo.
    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': True,
}