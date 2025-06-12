# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Campo para identificar si es un albarán de clasificación de devoluciones
    is_return_classification = fields.Boolean(
        'Es Clasificación de Devolución',
        compute='_compute_is_return_classification',
        store=True
    )

    # Campo para el destino de la devolución
    return_destination = fields.Selection([
        ('refurbish', 'Reacondicionar'),
        ('scrap', 'Desechar'),
        ('return_to_supplier', 'Devolver a Proveedor'),
        ('stock', 'Devolver a Stock')
    ], string='Destino de Devolución')

    # Campo para la fuente de la devolución (manual o API)
    return_source = fields.Selection([
        ('manual', 'Entrada Manual'),
        ('api', 'Importado de API')
    ], string='Fuente de Devolución', default='manual')

    # Referencia de la devolución en el mercado
    market_reference = fields.Char('Referencia del Mercado')

    # Fecha de devolución del mercado
    market_return_date = fields.Date('Fecha de Devolución del Mercado')

    # Motivo de la devolución
    return_reason = fields.Selection([
        ('damaged', 'Producto Dañado'),
        ('wrong_item', 'Producto Incorrecto'),
        ('quality_issue', 'Problema de Calidad'),
        ('customer_dissatisfaction', 'Cliente Insatisfecho'),
        ('other', 'Otro'),
    ], string='Motivo de Devolución')

    @api.depends('picking_type_id')
    def _compute_is_return_classification(self):
        """Determina si este albarán es una clasificación de devoluciones"""
        classification_type = self.env.ref('gestion_devoluciones.picking_type_returns_classification', False)
        for picking in self:
            picking.is_return_classification = classification_type and picking.picking_type_id.id == classification_type.id

    def action_apply_return_destination(self):
        """Aplica el destino seleccionado para la devolución"""
        self.ensure_one()

        if not self.return_destination:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Debe seleccionar un destino para la devolución'),
                    'sticky': False,
                    'type': 'danger',
                }
            }

        # Aquí iría la lógica para procesar la devolución según el destino seleccionado
        # Por ejemplo, crear movimientos a ubicaciones específicas o generar órdenes de trabajo

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Destino aplicado correctamente'),
                'sticky': False,
                'type': 'success',
            }
        }

    @api.model
    def fetch_market_returns(self):
        """Método para llamar a la API y descargar las devoluciones como albaranes"""
        try:
            # Configuración de la API - deberías almacenar estos valores en los parámetros del sistema
            api_url = self.env['ir.config_parameter'].sudo().get_param('market_api.url')
            api_key = self.env['ir.config_parameter'].sudo().get_param('market_api.key')

            if not api_url or not api_key:
                _logger.error("API URL o API Key no configurados")
                return False

            # Fecha de hoy para la consulta
            today = fields.Date.today()

            # Llamada a la API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            params = {
                'date_from': today.strftime('%Y-%m-%d'),
                'date_to': today.strftime('%Y-%m-%d')
            }

            response = requests.get(api_url, headers=headers, params=params)

            if response.status_code != 200:
                _logger.error(f"Error al obtener datos: {response.status_code} - {response.text}")
                return False

            returns_data = response.json()

            # Obtenemos el tipo de operación para clasificación de devoluciones
            classification_type = self.env.ref('gestion_devoluciones.picking_type_returns_classification', False)
            if not classification_type:
                _logger.error("No se encontró el tipo de operación para clasificación de devoluciones")
                return False

            # Ubicación de origen y destino para los albaranes
            location_src_id = classification_type.default_location_src_id.id
            location_dest_id = classification_type.default_location_dest_id.id

            # Contador de albaranes creados
            pickings_created = 0

            # Procesamos cada devolución de la API
            for return_item in returns_data.get('returns', []):
                # Buscamos el producto por referencia externa
                product = self.env['product.product'].search([
                    ('default_code', '=', return_item.get('product_code'))
                ], limit=1)

                if not product:
                    _logger.warning(f"Producto no encontrado: {return_item.get('product_code')}")
                    continue

                # Convertimos la razón de la API a nuestra razón interna
                return_reason = self._map_return_reason(return_item.get('reason'))

                # Creamos el albarán de devolución
                picking_vals = {
                    'picking_type_id': classification_type.id,
                    'location_id': location_src_id,
                    'location_dest_id': location_dest_id,
                    'origin': f"API Devolución: {return_item.get('reference')}",
                    'return_source': 'api',
                    'market_reference': return_item.get('reference'),
                    'market_return_date': return_item.get('return_date'),
                    'return_reason': return_reason,
                    'move_ids': [(0, 0, {
                        'name': product.name,
                        'product_id': product.id,
                        'product_uom_qty': float(return_item.get('quantity', 1.0)),
                        'product_uom': product.uom_id.id,
                        'location_id': location_src_id,
                        'location_dest_id': location_dest_id,
                    })]
                }

                # Creamos el albarán
                picking = self.create(picking_vals)
                pickings_created += 1

                # Opcionalmente, podemos confirmar el albarán automáticamente
                # picking.action_confirm()

            _logger.info(f"Se han importado {pickings_created} devoluciones desde la API")
            return True

        except Exception as e:
            _logger.exception(f"Error al procesar devoluciones del mercado: {str(e)}")
            return False

    @api.model
    def _map_return_reason(self, api_reason):
        """Mapea las razones de la API a las razones del sistema"""
        mapping = {
            'DAMAGED': 'damaged',
            'WRONG_ITEM': 'wrong_item',
            'QUALITY': 'quality_issue',
            'UNSATISFIED': 'customer_dissatisfaction',
        }
        return mapping.get(api_reason, 'other')