from odoo import models, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    empresa_origen_txt = fields.Char(string="Empresa Origen")