# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    market_api_url = fields.Char('URL de la API de Mercado', 
                                config_parameter='market_api.url')
    market_api_key = fields.Char('Clave de API', 
                                config_parameter='market_api.key')