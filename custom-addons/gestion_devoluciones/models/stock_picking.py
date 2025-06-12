# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_destination = fields.Selection([
        ('stock', 'Regresar a Stock'),
        ('warranty', 'Enviar a Garantía / Revisión')
    ], string='Acción de Devolución', default='stock')

    return_reason = fields.Selection([
        ('damaged', 'Producto Dañado'),
        ('wrong_item', 'Producto Incorrecto'),
        ('quality_issue', 'Problema de Calidad'),
        ('customer_dissatisfaction', 'Cliente Insatisfecho'),
        ('other', 'Otro'),
    ], string='Motivo de Devolución')

    is_return_picking_type = fields.Boolean(
        compute='_compute_is_return_picking_type'
    )

    @api.depends('picking_type_id')
    def _compute_is_return_picking_type(self):
        return_picking_type = self.env.ref('gestion_devoluciones.picking_type_returns', raise_if_not_found=False)
        for picking in self:
            picking.is_return_picking_type = (
                        return_picking_type and picking.picking_type_id.id == return_picking_type.id)

    def action_apply_return_destination(self):
        self.ensure_one()

        if self.state in ('done', 'cancel'):
            raise UserError(_("No se puede cambiar el destino de un albarán ya validado o cancelado."))

        if self.return_destination == 'warranty':
            destination_location = self.env.ref('gestion_devoluciones.stock_location_warranty')
            action_message = _("Destino cambiado a: %s") % (destination_location.display_name)
        else:  # 'stock'
            # ¡CAMBIO CLAVE!
            # El destino ahora es la ubicación de stock principal del almacén, no la
            # ubicación por defecto de la operación (que es 'Devoluciones').
            destination_location = self.picking_type_id.warehouse_id.lot_stock_id
            action_message = _("Destino cambiado a: %s") % (destination_location.display_name)

        if not destination_location:
            raise UserError(
                _("La ubicación de destino principal del almacén no pudo ser encontrada. Revisa la configuración."))

        self.move_lines.write({'location_dest_id': destination_location.id})
        self.message_post(body=action_message)
        return True