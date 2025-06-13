from odoo import models, fields, api

class InternalPurchaseOrder(models.Model):
    _name = 'internal.purchase.order'
    _description = 'Orden de Compra Interna'

    name = fields.Char(string="Referencia", required=True, default=lambda self: self.env['ir.sequence'].next_by_code('internal.purchase.order'))
    origen_location_id = fields.Many2one('stock.location', string="Ubicación Origen", required=True)
    destino_location_id = fields.Many2one('stock.location', string="Ubicación Destino", required=True)
    picking_id = fields.Many2one('stock.picking', string="Transferencia generada")
    line_ids = fields.One2many('internal.purchase.order.line', 'order_id', string="Líneas")
    company_id = fields.Many2one('res.company', related='destino_location_id.company_id', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Completado')
    ], default='draft')

    def action_confirm(self):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.origen_location_id.id,
            'location_dest_id': self.destino_location_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        })

        for line in self.line_ids:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': self.origen_location_id.id,
                'location_dest_id': self.destino_location_id.id,
                'company_id': self.company_id.id,
            })

        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

        self.picking_id = picking.id
        self.state = 'done'
