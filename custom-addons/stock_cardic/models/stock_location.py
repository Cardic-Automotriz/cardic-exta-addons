from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    empresa_origen_txt = fields.Char(string="Empresa Origen")