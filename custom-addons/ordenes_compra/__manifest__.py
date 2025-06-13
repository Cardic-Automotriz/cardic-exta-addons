{
    'name': 'Órdenes de Compra',
    'version': '1.0',
    'summary': 'Permite simular compras internas con traspasos entre ubicaciones',
    'author': 'TuNombre',
    'category': 'Inventory/Inventory',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/internal_purchase_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
