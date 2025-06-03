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

    show_aprobar_y_publicar = fields.Boolean(compute="_compute_show_aprobar_y_publicar", store=False)

    @api.depends('estado')
    def _compute_show_aprobar_y_publicar(self):
        for rec in self:
            rec.show_aprobar_y_publicar = rec.estado == 'revision'

    def action_aprobar_y_publicar(self):
        Job = self.env['hr.job']
        for solicitud in self:
            # Construir descripción extendida
            descripcion = solicitud.description or ''
            descripcion += f"\nNivel de estudios: {dict(self._fields['nivel_estudios'].selection).get(solicitud.nivel_estudios, '')}"
            descripcion += f"\nHorario: {dict(self._fields['horario'].selection).get(solicitud.horario, '')}"
            descripcion += f"\nSalario propuesto: {solicitud.salario} {solicitud.currency_id.name}"
            # Crear la vacante en hr.job
            job_vals = {
                'name': solicitud.name,
                'description': descripcion,
                'requirements': descripcion,
                # Puedes mapear más campos aquí si lo deseas
            }
            Job.create(job_vals)
            solicitud.estado = 'publicada' 