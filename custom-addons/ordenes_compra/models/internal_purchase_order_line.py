from odoo import models, fields

class InternalPurchaseOrderLine(models.Model):
    _name = 'internal.purchase.order.line'
    _description = 'Línea de la orden de compra interna'

    order_id = fields.Many2one('internal.purchase.order', required=True)
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(string="Cantidad", required=True)
