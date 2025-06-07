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


class Ruta(models.Model):
    _name = 'hr_cardic.ruta'
    _description = 'Ruta'

    name = fields.Char(string="Nombre de la Ruta", required=True)
    descripcion = fields.Text(string="Descripción")


class RhhDashboard(models.TransientModel):
    _name = 'hr_cardic.rhh_dashboard'
    _description = 'Panel RRHH'

    solicitudes_count = fields.Integer(string="Solicitudes de Vacante", compute="_compute_counts")
    vacantes_count = fields.Integer(string="Vacantes", compute="_compute_counts")
    empleados_count = fields.Integer(string="Empleados", compute="_compute_counts")
    asistencias_count = fields.Integer(string="Asistencias", compute="_compute_counts")
    vacaciones_count = fields.Integer(string="Faltas y Vacaciones", compute="_compute_counts")
    cajas_count = fields.Integer(string="Cajas", compute="_compute_counts")
    rutas_count = fields.Integer(string="Rutas", compute="_compute_counts")

    @api.depends()
    def _compute_counts(self):
        self.solicitudes_count = self.env['hr_cardic.solicitud'].search_count([])
        self.vacantes_count = self.env['hr.job'].search_count([])
        self.empleados_count = self.env['hr.employee'].search_count([])
        self.asistencias_count = self.env['hr.attendance'].search_count([])
        self.vacaciones_count = self.env['hr.leave'].search_count([])
        self.cajas_count = self.env['hr_cardic.caja'].search_count([])
        self.rutas_count = self.env['hr_cardic.ruta'].search_count([])

class CajaChica(models.Model):
    _name = 'hr_cardic.caja_chica'
    _description = 'Gestión de Caja Chica'

    name = fields.Selection([
        ('puebla', 'Puebla'),
        ('queretaro', 'Querétaro'),
        ('cuernavaca', 'Cuernavaca'),
        ('toluca', 'Toluca'),
        ('pachuca', 'Pachuca'),
    ], string="Nombre de la Ruta/Caja Chica", required=True)
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True)
    fecha_fin = fields.Date(string="Fecha de Fin", required=True)
    saldo_inicial = fields.Float(string="Saldo Inicial", required=True)
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('abierto', 'Abierto'),
        ('aprobado', 'Aprobado'),
    ], string="Estado", default='borrador', tracking=True)
    gastos_ids = fields.One2many('hr_cardic.gasto', 'caja_chica_id', string="Gastos")

    @api.depends('gastos_ids.subtotal', 'saldo_inicial')
    def _compute_total(self):
        for record in self:
            subtotal = sum(gasto.subtotal for gasto in record.gastos_ids)
            record.total = record.saldo_inicial - subtotal

    def action_abierto(self):
        for record in self:
            record.estado = 'abierto'

    def action_aprobar(self):
        for record in self:
            record.estado = 'aprobado'

class Gasto(models.Model):
    _name = 'hr_cardic.gasto'
    _description = 'Gestión de Gastos'

    caja_chica_id = fields.Many2one('hr_cardic.caja_chica', string="Caja Chica", required=True)
    fecha_gasto = fields.Date(string="Fecha del Gasto", required=True)
    concepto = fields.Char(string="Concepto", required=True)
    importe = fields.Float(string="Importe", required=True)
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends('importe')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.importe
