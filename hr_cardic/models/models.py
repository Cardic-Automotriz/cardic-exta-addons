from odoo import models, fields, api

class SolicitudVacante(models.Model):
    _name = 'hr_cardic.solicitud'
    _description = 'Solicitud de Vacante'

    name = fields.Char(string="Nombre de la Vacante", required=True)
    description = fields.Text(string="Descripción")
    jefe_solicitante = fields.Many2one('hr.employee', string="Jefe solicitante", required=True)
    nivel_estudios = fields.Selection([
        ('secundaria', 'Secundaria'),
        ('preparatoria', 'Preparatoria'),
        ('licenciatura', 'Licenciatura'),
        ('maestria', 'Maestría'),
        ('doctorado', 'Doctorado'),
    ], string="Nivel de estudios", default='licenciatura')
    horario = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
        ('tiempo_completo', 'Tiempo completo'),
    ], string="Horario", default='tiempo_completo')
    salario = fields.Monetary(string="Salario propuesto", default=10000.0, currency_field='currency_id')
    fecha_solicitud = fields.Datetime(string="Fecha de solicitud", default=fields.Datetime.now)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('revision', 'En revisión'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    ], string="Estado", default='borrador')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id) 