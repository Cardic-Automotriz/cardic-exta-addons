from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

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
            descripcion = solicitud.description or ''
            descripcion += f"\nNivel de estudios: {dict(self._fields['nivel_estudios'].selection).get(solicitud.nivel_estudios, '')}"
            descripcion += f"\nHorario: {dict(self._fields['horario'].selection).get(solicitud.horario, '')}"
            descripcion += f"\nSalario propuesto: {solicitud.salario} {solicitud.currency_id.name}"
            job_vals = {
                'name': solicitud.name,
                'description': descripcion,
                'requirements': descripcion,
            }
            Job.create(job_vals)
            solicitud.estado = 'publicada'

class Ruta(models.Model):
    _name = 'hr_cardic.ruta'
    _description = 'Rutas de Empleados'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, name'

    name = fields.Char(string="Nombre de la Ruta", required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, tracking=True)
    fecha = fields.Date(string="Fecha", required=True, default=fields.Date.today, tracking=True)
    zona = fields.Selection([
        ('puebla', 'Puebla'),
        ('cuernavaca', 'Cuernavaca'),
        ('queretaro', 'Querétaro'),
        ('toluca', 'Toluca'),
        ('pachuca', 'Pachuca'),
    ], string="Zona", required=True, tracking=True)
    
    task_id = fields.Many2one('project.task', string="Tarea Relacionada")
    hora_inicio = fields.Datetime(string="Hora de Inicio", tracking=True)
    hora_fin = fields.Datetime(string="Hora de Finalización", tracking=True)
    duracion = fields.Float(string="Duración (Horas)", compute='_compute_duracion', store=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_progreso', 'En Progreso'),
        ('finalizado', 'Finalizado'),
        ('aprobado', 'Aprobado')
    ], string="Estado", default='borrador', tracking=True)
    
    # Campos contables
    saldo_inicial = fields.Monetary(string="Saldo Inicial", tracking=True, required=True)
    saldo_actual = fields.Monetary(string="Saldo Actual", compute='_compute_saldo_actual', store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', 
        default=lambda self: self.env.company.currency_id.id, required=True)
    cuenta_analitica_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    gastos_ids = fields.One2many('hr_cardic.gasto_ruta', 'ruta_id', string="Gastos")
    company_id = fields.Many2one('res.company', string='Compañía', 
        default=lambda self: self.env.company.id, required=True)
    caja_chica_id = fields.Many2one('hr_cardic.caja_chica', string="Caja Chica Asociada")

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for ruta in self:
            if ruta.hora_inicio and ruta.hora_fin:
                duracion = (ruta.hora_fin - ruta.hora_inicio).total_seconds() / 3600
                ruta.duracion = round(duracion, 2)
            else:
                ruta.duracion = 0.0

    @api.depends('saldo_inicial', 'gastos_ids.importe')
    def _compute_saldo_actual(self):
        for ruta in self:
            total_gastos = sum(ruta.gastos_ids.mapped('importe'))
            ruta.saldo_actual = ruta.saldo_inicial - total_gastos

    def action_iniciar(self):
        self.write({
            'estado': 'en_progreso',
            'hora_inicio': fields.Datetime.now()
        })

    def action_finalizar(self):
        self.write({
            'estado': 'finalizado',
            'hora_fin': fields.Datetime.now()
        })

    def action_aprobar(self):
        self.write({'estado': 'aprobado'})

    def action_borrador(self):
        if self.estado != 'aprobado':
            self.write({'estado': 'borrador'})

    @api.constrains('saldo_inicial')
    def _check_saldo_inicial(self):
        for ruta in self:
            if ruta.saldo_inicial <= 0:
                raise ValidationError('El saldo inicial debe ser mayor que 0.')

    @api.model
    def create(self, vals):
        ruta = super().create(vals)
        # Crear la caja chica asociada
        caja_vals = {
            'name': ruta.zona,
            'fecha_inicio': ruta.fecha,
            'fecha_fin': ruta.fecha,
            'saldo_inicial': ruta.saldo_inicial,
            'estado': 'borrador',
        }
        caja = self.env['hr_cardic.caja_chica'].create(caja_vals)
        ruta.write({'caja_chica_id': caja.id})

        # Buscar el usuario admin (puedes cambiar el login si quieres otro usuario)
        admin_user = self.env.ref('base.user_admin')
        if admin_user.partner_id:
            # Agregar admin como seguidor si no lo es
            ruta.message_subscribe(partner_ids=[admin_user.partner_id.id])
            # Mandar mensaje al chatter y notificar
            ruta.message_post(
                body=f'Se ha creado la ruta <b>{ruta.name}</b> y la caja chica asociada.',
                subject='Nueva Ruta y Caja Chica',
                partner_ids=[admin_user.partner_id.id],
                message_type='notification'
            )
        return ruta

class GastoRuta(models.Model):
    _name = 'hr_cardic.gasto_ruta'
    _description = 'Gastos de Ruta'
    _order = 'fecha desc'

    ruta_id = fields.Many2one('hr_cardic.ruta', string="Ruta", required=True)
    fecha = fields.Date(string="Fecha", required=True, default=fields.Date.today)
    concepto = fields.Char(string="Concepto", required=True)
    importe = fields.Monetary(string="Importe", required=True)
    currency_id = fields.Many2one('res.currency', related='ruta_id.currency_id', store=True)
    notas = fields.Text(string="Notas")
    company_id = fields.Many2one('res.company', related='ruta_id.company_id', store=True)
    
    # Campos contables
    cuenta_id = fields.Many2one('account.account', string='Cuenta Contable', 
        domain="[('company_id', '=', company_id)]", required=True)
    cuenta_analitica_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica',
        related='ruta_id.cuenta_analitica_id', store=True)
    
    @api.constrains('importe')
    def _check_importe(self):
        for gasto in self:
            if gasto.importe <= 0:
                raise ValidationError('El importe debe ser mayor que 0.')
            if gasto.importe > gasto.ruta_id.saldo_actual:
                raise ValidationError('El gasto no puede ser mayor que el saldo actual.')

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
    encuestas_count = fields.Integer(string="Evaluaciones/Entrevistas", compute="_compute_counts")

    @api.depends()
    def _compute_counts(self):
        self.solicitudes_count = self.env['hr_cardic.solicitud'].search_count([])
        self.vacantes_count = self.env['hr.job'].search_count([])
        self.empleados_count = self.env['hr.employee'].search_count([])
        self.asistencias_count = self.env['hr.attendance'].search_count([])
        self.vacaciones_count = self.env['hr.leave'].search_count([])
        self.cajas_count = self.env['hr_cardic.caja_chica'].search_count([])
        self.rutas_count = self.env['hr_cardic.ruta'].search_count([])
        self.encuestas_count = self.env['survey.survey'].search_count([])

class CajaChica(models.Model):
    _name = 'hr_cardic.caja_chica'
    _description = 'Gestión de Caja Chica'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    caja_chica_id = fields.Many2one('hr_cardic.caja_chica', string='Caja Chica')
    ruta_id = fields.Many2one('hr_cardic.ruta', string='Ruta')

    # Opcional: sincronizar ruta automáticamente si se selecciona una caja chica
    @api.onchange('caja_chica_id')
    def _onchange_caja_chica_id(self):
        if self.caja_chica_id and self.caja_chica_id.ruta_ids:
            self.ruta_id = self.caja_chica_id.ruta_ids[0]
