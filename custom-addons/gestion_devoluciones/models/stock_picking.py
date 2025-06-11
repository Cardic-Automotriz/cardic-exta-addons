from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Campo para que el usuario elija qué hacer con la devolución
    return_destination = fields.Selection(
        [
            ('picking', 'Reingresar a Picking'),
            ('warranty', 'Enviar a Garantía'),
        ],
        string="Destino de la Devolución",
        copy=False
    )

    def action_process_return(self):
        """
        Procesa la devolución moviendo los productos a la ubicación final
        seleccionada por el usuario.
        """
        self.ensure_one()

        if self.state not in ('assigned', 'done'):
            raise UserError(
                _("La devolución debe estar lista para procesar (en estado 'Preparado') o ya 'Hecho' si es un ajuste."))

        if not self.return_destination:
            raise UserError(_("Por favor, selecciona un destino para los productos devueltos."))

        # Buscar las ubicaciones de destino
        if self.return_destination == 'picking':
            # La ubicación de 'picking' o empaquetado del almacén
            destination_location = self.picking_type_id.warehouse_id.wh_pack_stock_loc_id
            if not destination_location:
                raise UserError(_("No se pudo encontrar la ubicación de picking para el almacén."))
        else:  # 'warranty'
            destination_location = self.env.ref('gestion_devoluciones.stock_location_warranty')

        # Cambiamos la ubicación de destino de todos los movimientos de la transferencia
        self.move_lines.write({'location_dest_id': destination_location.id})

        # Si la transferencia no está validada, la validamos para que se ejecute el movimiento de stock
        if self.state != 'done':
            self.button_validate()

        return True
