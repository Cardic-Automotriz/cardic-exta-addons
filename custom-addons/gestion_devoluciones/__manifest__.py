{
    'name': "Gestión de Devoluciones",
    'summary': "Módulo para gestionar el proceso de devoluciones de clientes.",
    'description': """
        Este módulo añade nuevas ubicaciones y tipos de operación para manejar
        las devoluciones de productos y su posterior inspección o proceso de garantía.
    """,
    'author': "Tu Nombre",
    'website': "https://www.tuweb.com",
    'category': 'Inventory/Inventory',
    'version': '17.0.1.0.0',

    # --- LÍNEA CLAVE ---
    # Asegúrate de que 'stock' esté en la lista de dependencias.
    'depends': ['base', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': True,
}