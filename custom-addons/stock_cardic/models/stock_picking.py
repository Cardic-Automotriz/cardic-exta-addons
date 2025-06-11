from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    empresa_origen_txt = fields.Char(string="Empresa Origen")