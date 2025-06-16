from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import requests
import json

class SolicitudVacante(models.Model):
    _name = 'hr_cardic.solicitud'
    _description = 'Solicitud de Vacante'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    active = fields.Boolean(default=True, string="Activo")

    name = fields.Char(string="Nombre de la Vacante", required=True, tracking=True)
    description = fields.Text(string="Descripción", tracking=True)
    jefe_solicitante = fields.Many2one('hr.employee', string="Jefe solicitante", required=True, tracking=True)
    nivel_estudios = fields.Selection([
        ('secundaria', 'Secundaria'),
        ('preparatoria', 'Preparatoria'),
        ('licenciatura', 'Licenciatura'),
        ('maestria', 'Maestría'),
        ('doctorado', 'Doctorado'),
    ], string="Nivel de estudios", default='licenciatura', tracking=True)
    horario = fields.Selection([
        ('matutino', 'Matutino'),
        ('vespertino', 'Vespertino'),
        ('nocturno', 'Nocturno'),
        ('tiempo_completo', 'Tiempo completo'),
    ], string="Horario", default='tiempo_completo', tracking=True)
    salario = fields.Monetary(string="Salario propuesto", default=10000.0, currency_field='currency_id', tracking=True)
    fecha_solicitud = fields.Datetime(string="Fecha de solicitud", default=fields.Datetime.now, tracking=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('revision', 'En revisión'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    ], string="Estado", default='borrador', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id)
    linkedin_job_id = fields.Char(string='ID de Vacante LinkedIn', readonly=True)
    linkedin_url = fields.Char(string='URL de Vacante LinkedIn', readonly=True)
    publicar_linkedin = fields.Boolean(string='Publicar en LinkedIn', default=True, tracking=True)

    show_aprobar_y_publicar = fields.Boolean(compute="_compute_show_aprobar_y_publicar", store=False)

    @api.depends('estado')
    def _compute_show_aprobar_y_publicar(self):
        for rec in self:
            rec.show_aprobar_y_publicar = rec.estado == 'revision'

    def _prepare_job_data(self):
        """Preparar datos de la vacante para LinkedIn"""
        self.ensure_one()
        
        # Construir la descripción completa
        descripcion = self.description or ''
        descripcion += f"\n\nRequisitos:"
        descripcion += f"\n• Nivel de estudios: {dict(self._fields['nivel_estudios'].selection).get(self.nivel_estudios, '')}"
        descripcion += f"\n• Horario: {dict(self._fields['horario'].selection).get(self.horario, '')}"
        descripcion += f"\n• Salario: {self.salario} {self.currency_id.name}"
        
        # URL de aplicación (puedes personalizar esto según tu configuración)
        application_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/jobs/apply/{self.id}"
        
        return {
            'name': self.name,
            'description': descripcion,
            'application_url': application_url
        }

    def action_aprobar_y_publicar(self):
        for solicitud in self:
            # Crear la vacante en Odoo
            Job = self.env['hr.job']
            job_vals = {
                'name': solicitud.name,
                'description': solicitud.description,
                'requirements': solicitud.description,
            }
            job = Job.create(job_vals)
            
            # Publicar en LinkedIn si está habilitado
            if solicitud.publicar_linkedin:
                try:
                    linkedin_config = self.env['hr_cardic.linkedin_config'].get_active_config()
                    job_data = solicitud._prepare_job_data()
                    response = linkedin_config.publish_job(job_data)
                    
                    # Actualizar la solicitud con la información de LinkedIn
                    solicitud.write({
                        'linkedin_job_id': response.get('id'),
                        'linkedin_url': response.get('url'),
                        'estado': 'publicada'
                    })
                    
                    # Notificar al solicitante
                    solicitud.message_post(
                        body=f"La vacante ha sido publicada en LinkedIn. URL: {response.get('url')}",
                        message_type='comment'
                    )
                except Exception as e:
                    solicitud.message_post(
                        body=f"Error al publicar en LinkedIn: {str(e)}",
                        message_type='comment'
                    )
                    raise ValidationError(f"Error al publicar en LinkedIn: {str(e)}")
            else:
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

class Finiquito(models.Model):
    _name = 'hr_cardic.finiquito'
    _description = 'Finiquito'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string="Contrato", tracking=True)
    fecha_inicio = fields.Date(related='contract_id.date_start', string="Fecha de Inicio", store=True, tracking=True)
    fecha_fin = fields.Date(string="Fecha de Término", tracking=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='contract_id.currency_id', store=True)
    salario = fields.Monetary(related='contract_id.wage', string="Salario", currency_field='currency_id', store=True, tracking=True)
    dias_trabajados = fields.Integer(string="Días trabajados", compute="_compute_fields_liq", store=True)
    anios_trabajados = fields.Float(string="Años trabajados", compute="_compute_fields_liq", store=True)
    salario_diario = fields.Float(string="Salario diario", compute="_compute_fields_liq", store=True)
    dias_aguinaldo = fields.Integer(string="Días de aguinaldo", default=15, tracking=True)
    primer_dia_ano = fields.Date(string="Primer día del año", compute="_compute_aguinaldo_liq", store=True)
    dias_trabajados_aguinaldo = fields.Integer(string="Días trabajados para aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    factor_aguinaldo = fields.Float(string="Factor de aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    dias_que_corresponde = fields.Float(string="Días que corresponde", compute="_compute_aguinaldo_liq", store=True)
    proporcional_aguinaldo = fields.Float(string="Proporcional de aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    anios_cumplidos = fields.Integer(string="Años cumplidos", compute="_compute_vacaciones_liq", store=True)
    dias_vacaciones = fields.Integer(string="Días de vacaciones", compute="_compute_vacaciones_liq", store=True)
    factor_vacaciones = fields.Float(string="Factor para vacaciones", compute="_compute_vacaciones_liq", store=True)
    dias_que_le_corresponde = fields.Float(string="Días que le corresponde", compute="_compute_vacaciones_liq", store=True)
    proporcional_vacaciones_sin_2022 = fields.Float(string="Proporcional para vacaciones", compute="_compute_vacaciones_liq", store=True)
    porcentaje_prima = fields.Float(string="Porcentaje de la prima", default=25, tracking=True)
    prima_vacacional = fields.Float(string="Prima vacacional", compute="_compute_prima_vacacional_liq", store=True)
    salario_proporcional = fields.Float(string="Salario proporcional", compute="_compute_salario_proporcional", store=True)
    bono = fields.Float(string="Bono", default=0.0)
    # Variables internas (no visibles en Odoo)
    exento_aguinaldo = fields.Float(string="Exento de aguinaldo", compute="_compute_impuestos_proporcionales", store=True)
    exento_prima_vacacional = fields.Float(string="Exento de prima vacacional", compute="_compute_impuestos_proporcionales", store=True)
    exento_bono = fields.Float(string="Exento de bono", compute="_compute_impuestos_proporcionales", store=True)
    limite_inferior = fields.Float(string="Límite inferior ISR", compute="_compute_impuestos_proporcionales", store=True)
    limite_superior = fields.Float(string="Límite superior ISR", compute="_compute_impuestos_proporcionales", store=True)
    cuota_fija = fields.Float(string="Cuota fija ISR", compute="_compute_impuestos_proporcionales", store=True)
    porcentaje_excedente = fields.Float(string="% sobre excedente ISR", compute="_compute_impuestos_proporcionales", store=True)
    # Campos visibles
    gravamen_aguinaldo = fields.Float(string="Gravamen de aguinaldo", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_prima_vacacional = fields.Float(string="Gravamen de prima vacacional", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_bono = fields.Float(string="Gravamen de bono", compute="_compute_impuestos_proporcionales", store=True)
    total_gravamenes = fields.Float(string="Total de gravámenes", compute="_compute_impuestos_proporcionales", store=True)
    calculo_1 = fields.Float(string="Cálculo 1 ISR", compute="_compute_impuestos_proporcionales", store=True)
    calculo_2 = fields.Float(string="Cálculo 2 ISR", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_proporcionales = fields.Float(string="Gravamen de proporcionales", compute="_compute_impuestos_proporcionales", store=True)
    # FI y SDI
    fi1 = fields.Float(string="FI1", compute="_compute_fi_sdi", store=True)
    fi2 = fields.Float(string="FI2", compute="_compute_fi_sdi", store=True)
    sdi = fields.Float(string="SDI", compute="_compute_fi_sdi", store=True)
    dias_trabajados_quincena = fields.Integer(string="Días trabajados a la quincena", compute="_compute_fi_sdi", store=True)

    # Enfermedades y maternidad
    en_especie = fields.Float(string="En especie (IMSS)", compute="_compute_imss_fields", store=True)
    roimss = fields.Float(string="Gravamen de ROIMSS", compute="_compute_imss_fields", store=True)
    excedente = fields.Float(string="Excedente (IMSS)", compute="_compute_imss_fields", store=True)
    gastos_medicos = fields.Float(string="Gastos médicos para pensionados y beneficiados", compute="_compute_imss_fields", store=True)
    en_dinero = fields.Float(string="En dinero (IMSS)", compute="_compute_imss_fields", store=True)

    # Invalidez y vida
    invalidez_vida = fields.Float(string="En especie y dinero (Invalidez y vida)", compute="_compute_imss_fields", store=True)

    # Retiro, Cesantía en Edad Avanzada y Vejez
    cv = fields.Float(string="CV (Retiro, Cesantía y Vejez)", compute="_compute_imss_fields", store=True)

    # Total de indemnizaciones de IMSS
    total_imss = fields.Float(string="Total de indemnizaciones de IMSS", compute="_compute_imss_fields", store=True)

    @api.onchange('employee_id')
    def _onchange_employee_id_liq(self):
        if self.employee_id:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)
            self.contract_id = contract
        else:
            self.contract_id = False

    @api.depends('fecha_inicio', 'fecha_fin', 'salario')
    def _compute_fields_liq(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin:
                dias = (rec.fecha_fin - rec.fecha_inicio).days + 1
                dias = round(dias, 2)
                rec.dias_trabajados = dias
                anios_trabajados = round(dias / 365 if dias else 0.0, 2)
                rec.anios_trabajados = anios_trabajados
            else:
                rec.dias_trabajados = 0
                rec.anios_trabajados = 0.0
            salario_diario = round((rec.salario / 2) / 15 if rec.salario else 0.0, 2)
            rec.salario_diario = salario_diario

    @api.depends('fecha_fin', 'salario_diario', 'dias_aguinaldo')
    def _compute_aguinaldo_liq(self):
        from datetime import date
        for rec in self:
            if rec.fecha_fin:
                primer_dia = date(rec.fecha_fin.year, 1, 1)
                rec.primer_dia_ano = primer_dia
                dias_trab = (rec.fecha_fin - primer_dia).days + 1
                dias_trab = round(dias_trab, 2)
                rec.dias_trabajados_aguinaldo = dias_trab
                factor_aguinaldo = round(dias_trab / 365 if dias_trab else 0.0, 2)
                rec.factor_aguinaldo = factor_aguinaldo
                dias_que_corresponde = round(rec.dias_aguinaldo * factor_aguinaldo, 2)
                rec.dias_que_corresponde = dias_que_corresponde
                proporcional_aguinaldo = round(dias_que_corresponde * rec.salario_diario, 2)
                rec.proporcional_aguinaldo = proporcional_aguinaldo
            else:
                rec.primer_dia_ano = False
                rec.dias_trabajados_aguinaldo = 0
                rec.factor_aguinaldo = 0.0
                rec.dias_que_corresponde = 0.0
                rec.proporcional_aguinaldo = 0.0

    @api.depends('anios_trabajados', 'salario_diario')
    def _compute_vacaciones_liq(self):
        for rec in self:
            anios_trabajados = round(rec.anios_trabajados or 0.0, 2)
            anios_cumplidos = int(anios_trabajados)
            rec.anios_cumplidos = anios_cumplidos
            if anios_cumplidos <= 1:
                dias_vac = 12
            elif anios_cumplidos == 2:
                dias_vac = 14
            elif anios_cumplidos == 3:
                dias_vac = 16
            elif anios_cumplidos == 4:
                dias_vac = 18
            elif anios_cumplidos == 5:
                dias_vac = 20
            elif 6 <= anios_cumplidos <= 10:
                dias_vac = 22
            elif 11 <= anios_cumplidos <= 15:
                dias_vac = 24
            elif 16 <= anios_cumplidos <= 20:
                dias_vac = 26
            elif 21 <= anios_cumplidos <= 25:
                dias_vac = 28
            else:
                dias_vac = 0
            rec.dias_vacaciones = dias_vac
            factor_vac = round(anios_trabajados - anios_cumplidos if anios_trabajados else 0.0, 2)
            rec.factor_vacaciones = factor_vac
            dias_corresponde = round(factor_vac * dias_vac, 2)
            rec.dias_que_le_corresponde = dias_corresponde
            proporcional_vacaciones_sin_2022 = round(dias_corresponde * rec.salario_diario, 2)
            rec.proporcional_vacaciones_sin_2022 = proporcional_vacaciones_sin_2022

    @api.depends('proporcional_vacaciones_sin_2022', 'porcentaje_prima')
    def _compute_prima_vacacional_liq(self):
        for rec in self:
            porcentaje = round((rec.porcentaje_prima or 0) / 100.0, 2)
            rec.prima_vacacional = round(rec.proporcional_vacaciones_sin_2022 * porcentaje, 2)

    @api.depends('salario_diario', 'anios_cumplidos', 'anios_trabajados')
    def _compute_salario_proporcional(self):
        from datetime import date
        for rec in self:
            if rec.fecha_fin and rec.salario_diario:
                # Determinar el día de corte (1 o 15 del mes)
                dia = rec.fecha_fin.day
                if dia > 15:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 15)
                else:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 1)
                dias = (rec.fecha_fin - corte).days + 1
                dias = dias if dias > 0 else 0
                rec.salario_proporcional = round(dias * rec.salario_diario, 2)
            else:
                rec.salario_proporcional = 0.0

    @api.depends('salario_proporcional', 'proporcional_aguinaldo', 'prima_vacacional', 'bono', 'proporcional_vacaciones_sin_2022')
    def _compute_impuestos_proporcionales(self):
        TABLA_ISR = [
            {"lim_inf": 0.01, "lim_sup": 368.10, "cuota_fija": 0.00, "porcentaje": 1.92},
            {"lim_inf": 368.11, "lim_sup": 3124.35, "cuota_fija": 7.05, "porcentaje": 6.40},
            {"lim_inf": 3124.36, "lim_sup": 5490.75, "cuota_fija": 183.45, "porcentaje": 10.88},
            {"lim_inf": 5490.76, "lim_sup": 6382.80, "cuota_fija": 441.00, "porcentaje": 16.00},
            {"lim_inf": 6382.81, "lim_sup": 7641.90, "cuota_fija": 583.65, "porcentaje": 17.92},
            {"lim_inf": 7641.91, "lim_sup": 15412.80, "cuota_fija": 809.25, "porcentaje": 21.36},
            {"lim_inf": 15412.81, "lim_sup": 24292.65, "cuota_fija": 2469.15, "porcentaje": 23.52},
            {"lim_inf": 24292.66, "lim_sup": 46378.50, "cuota_fija": 4557.75, "porcentaje": 30.00},
            {"lim_inf": 46378.51, "lim_sup": 61838.10, "cuota_fija": 11183.40, "porcentaje": 32.00},
            {"lim_inf": 61838.11, "lim_sup": 185514.31, "cuota_fija": 16130.55, "porcentaje": 34.00},
            {"lim_inf": 185514.31, "lim_sup": float('inf'), "cuota_fija": 58180.35, "porcentaje": 35.00},
        ]
        for rec in self:
            # Exentos
            rec.exento_aguinaldo = round(30 * 113.14, 2)
            rec.exento_prima_vacacional = round(15 * 113.14, 2)
            rec.exento_bono = round(5 * 113.14, 2)
            # Gravámenes
            rec.gravamen_aguinaldo = round(rec.proporcional_aguinaldo - rec.exento_aguinaldo, 2) if (rec.proporcional_aguinaldo or 0) > rec.exento_aguinaldo else 0.0
            rec.gravamen_prima_vacacional = round(rec.prima_vacacional - rec.exento_prima_vacacional, 2) if (rec.prima_vacacional or 0) > rec.exento_prima_vacacional else 0.0
            rec.gravamen_bono = round(rec.bono - rec.exento_bono, 2) if (rec.bono or 0) > rec.exento_bono else 0.0
            # Total de gravámenes
            rec.total_gravamenes = round((rec.salario_proporcional or 0) + (rec.proporcional_vacaciones_sin_2022 or 0) + rec.gravamen_aguinaldo + rec.gravamen_prima_vacacional + rec.gravamen_bono, 2)
            # Buscar rango ISR
            fila = next((f for f in TABLA_ISR if f["lim_inf"] <= rec.total_gravamenes <= f["lim_sup"]), None)
            if fila:
                rec.limite_inferior = fila["lim_inf"]
                rec.limite_superior = fila["lim_sup"]
                rec.cuota_fija = fila["cuota_fija"]
                rec.porcentaje_excedente = fila["porcentaje"]
                rec.calculo_1 = round(rec.total_gravamenes - rec.limite_inferior, 2)
                rec.calculo_2 = round(rec.calculo_1 * (rec.porcentaje_excedente / 100), 2)
                rec.gravamen_proporcionales = round(rec.calculo_2 + rec.cuota_fija, 2)
            else:
                rec.limite_inferior = 0.0
                rec.limite_superior = 0.0
                rec.cuota_fija = 0.0
                rec.porcentaje_excedente = 0.0
                rec.calculo_1 = 0.0
                rec.calculo_2 = 0.0
                rec.gravamen_proporcionales = 0.0

    def action_descargar_finiquito(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_cardic.reporte_finiquito_pdf_template',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'res_model': self._name,
        }

    @api.depends('salario_diario', 'fecha_fin')
    def _compute_fi_sdi(self):
        from datetime import date
        for rec in self:
            # FI1 y FI2
            fi1 = 365 + 15 + ((rec.dias_vacaciones or 0) * 0.25)
            rec.fi1 = fi1
            fi2 = fi1 / 365
            rec.fi2 = fi2
            rec.sdi = round(fi2 * (rec.salario_diario or 0), 2)
            # Días trabajados a la quincena
            if rec.fecha_fin:
                dia = rec.fecha_fin.day
                if dia > 15:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 15)
                else:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 1)
                dias = (rec.fecha_fin - corte).days + 1
                dias = dias if dias > 0 else 0
                rec.dias_trabajados_quincena = dias
            else:
                rec.dias_trabajados_quincena = 0

    @api.depends('sdi', 'dias_trabajados_quincena')
    def _compute_imss_fields(self):
        for rec in self:
            # Enfermedades y maternidad
            rec.en_especie = round(3 * 113.14, 2)
            rec.roimss = round((rec.sdi or 0) - rec.en_especie, 2)
            rec.excedente = round(rec.roimss * 0.004, 2)
            rec.gastos_medicos = round(0.00375 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            rec.en_dinero = round(0.0025 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Invalidez y vida
            rec.invalidez_vida = round(0.00625 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Retiro, Cesantía y Vejez
            rec.cv = round(0.01125 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Total IMSS
            rec.total_imss = round((rec.excedente or 0) + (rec.gastos_medicos or 0) + (rec.en_dinero or 0) + (rec.invalidez_vida or 0) + (rec.cv or 0), 2)


class Liquidacion(models.Model):
    _name = 'hr_cardic.liquidacion'
    _description = 'Liquidación'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string="Contrato", tracking=True)
    fecha_inicio = fields.Date(related='contract_id.date_start', string="Fecha de Inicio", store=True, tracking=True)
    fecha_fin = fields.Date(string="Fecha de Término", tracking=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='contract_id.currency_id', store=True)
    salario = fields.Monetary(related='contract_id.wage', string="Salario", currency_field='currency_id', store=True, tracking=True)
    dias_trabajados = fields.Integer(string="Días trabajados", compute="_compute_fields_liq", store=True)
    anios_trabajados = fields.Float(string="Años trabajados", compute="_compute_fields_liq", store=True)
    salario_diario = fields.Float(string="Salario diario", compute="_compute_fields_liq", store=True)
    dias_aguinaldo = fields.Integer(string="Días de aguinaldo", default=15, tracking=True)
    primer_dia_ano = fields.Date(string="Primer día del año", compute="_compute_aguinaldo_liq", store=True)
    dias_trabajados_aguinaldo = fields.Integer(string="Días trabajados para aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    factor_aguinaldo = fields.Float(string="Factor de aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    dias_que_corresponde = fields.Float(string="Días que corresponde", compute="_compute_aguinaldo_liq", store=True)
    proporcional_aguinaldo = fields.Float(string="Proporcional de aguinaldo", compute="_compute_aguinaldo_liq", store=True)
    anios_cumplidos = fields.Integer(string="Años cumplidos", compute="_compute_vacaciones_liq", store=True)
    dias_vacaciones = fields.Integer(string="Días de vacaciones", compute="_compute_vacaciones_liq", store=True)
    factor_vacaciones = fields.Float(string="Factor para vacaciones", compute="_compute_vacaciones_liq", store=True)
    dias_que_le_corresponde = fields.Float(string="Días que le corresponde", compute="_compute_vacaciones_liq", store=True)
    proporcional_vacaciones_sin_2022 = fields.Float(string="Proporcional para vacaciones", compute="_compute_vacaciones_liq", store=True)
    porcentaje_prima = fields.Float(string="Porcentaje de la prima", default=25, tracking=True)
    prima_vacacional = fields.Float(string="Prima vacacional", compute="_compute_prima_vacacional_liq", store=True)
    # Indemnización y antigüedad
    indemnizacion = fields.Float(string="Indemnización", compute="_compute_indemnizacion_liq", store=True)
    veinte_dias_por_anio = fields.Float(string="20 días por año", compute="_compute_indemnizacion_liq", store=True)
    prima_antiguedad = fields.Float(string="Prima de antigüedad", compute="_compute_indemnizacion_liq", store=True)
    # Impuestos de indemnización
    monto_exento_indemnizacion = fields.Float(string="Monto exento de indemnización", compute="_compute_impuestos_indemnizacion", store=True, digits=(16, 4))
    salario_mensual_ordinario = fields.Float(string="Salario Mensual Ordinario", compute="_compute_isr_liquidacion", store=True, digits=(16, 4))
    excedente1 = fields.Float(string="Excedente", compute="_compute_isr_liquidacion", store=True, digits=(16, 4))
    factor_conversion = fields.Float(string="Factor de conversión", compute="_compute_isr_liquidacion", store=True, digits=(16, 4))
    importe_gravado = fields.Float(string="Importe gravado", compute="_compute_isr_liquidacion_final", store=True, digits=(16, 4))
    retencion_isr = fields.Float(string="Retención de ISR", compute="_compute_isr_liquidacion_final", store=True, digits=(16, 4))
    total_indemnizacion = fields.Float(string="Total de Indemnización", compute="_compute_isr_liquidacion_final", store=True, digits=(16, 4))
    gravado_prima_antiguedad = fields.Float(string="Gravado de Prima de Antigüedad", compute="_compute_prima_antiguedad_liq", store=True, digits=(16, 4))
    retencion_prima_antiguedad = fields.Float(string="Retención de Prima de Antigüedad", compute="_compute_prima_antiguedad_liq", store=True, digits=(16, 4))
    total_indemnizacion_prima_antiguedad = fields.Float(string="Total de Indemnización de Prima de Antigüedad", compute="_compute_prima_antiguedad_liq", store=True, digits=(16, 4))
    gravamen_veinte_dias = fields.Float(string="Gravamen de 20 días por año", compute="_compute_veinte_dias_impuestos", store=True, digits=(16, 4))
    retencion_veinte_dias = fields.Float(string="Retención de 20 días por año", compute="_compute_veinte_dias_impuestos", store=True, digits=(16, 4))
    total_indemnizacion_veinte_dias = fields.Float(string="Total de indemnización de 20 días por año", compute="_compute_veinte_dias_impuestos", store=True, digits=(16, 4))
    salario_proporcional = fields.Float(string="Salario proporcional", compute="_compute_salario_proporcional", store=True)
    bono = fields.Float(string="Bono", default=0.0)
    # Variables internas (no visibles en Odoo)
    exento_aguinaldo = fields.Float(string="Exento de aguinaldo", compute="_compute_impuestos_proporcionales", store=True)
    exento_prima_vacacional = fields.Float(string="Exento de prima vacacional", compute="_compute_impuestos_proporcionales", store=True)
    exento_bono = fields.Float(string="Exento de bono", compute="_compute_impuestos_proporcionales", store=True)
    limite_inferior = fields.Float(string="Límite inferior ISR", compute="_compute_impuestos_proporcionales", store=True)
    limite_superior = fields.Float(string="Límite superior ISR", compute="_compute_impuestos_proporcionales", store=True)
    cuota_fija = fields.Float(string="Cuota fija ISR", compute="_compute_impuestos_proporcionales", store=True)
    porcentaje_excedente = fields.Float(string="% sobre excedente ISR", compute="_compute_impuestos_proporcionales", store=True)
    # Campos visibles
    gravamen_aguinaldo = fields.Float(string="Gravamen de aguinaldo", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_prima_vacacional = fields.Float(string="Gravamen de prima vacacional", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_bono = fields.Float(string="Gravamen de bono", compute="_compute_impuestos_proporcionales", store=True)
    total_gravamenes = fields.Float(string="Total de gravámenes", compute="_compute_impuestos_proporcionales", store=True)
    calculo_1 = fields.Float(string="Cálculo 1 ISR", compute="_compute_impuestos_proporcionales", store=True)
    calculo_2 = fields.Float(string="Cálculo 2 ISR", compute="_compute_impuestos_proporcionales", store=True)
    gravamen_proporcionales = fields.Float(string="Gravamen de proporcionales", compute="_compute_impuestos_proporcionales", store=True)
    # FI y SDI
    fi1 = fields.Float(string="FI1", compute="_compute_fi_sdi", store=True)
    fi2 = fields.Float(string="FI2", compute="_compute_fi_sdi", store=True)
    sdi = fields.Float(string="SDI", compute="_compute_fi_sdi", store=True)
    dias_trabajados_quincena = fields.Integer(string="Días trabajados a la quincena", compute="_compute_fi_sdi", store=True)

    # Enfermedades y maternidad
    en_especie = fields.Float(string="En especie (IMSS)", compute="_compute_imss_fields", store=True)
    roimss = fields.Float(string="Gravamen de ROIMSS", compute="_compute_imss_fields", store=True)
    excedente = fields.Float(string="Excedente (IMSS)", compute="_compute_imss_fields", store=True)
    gastos_medicos = fields.Float(string="Gastos médicos para pensionados y beneficiados", compute="_compute_imss_fields", store=True)
    en_dinero = fields.Float(string="En dinero (IMSS)", compute="_compute_imss_fields", store=True)

    # Invalidez y vida
    invalidez_vida = fields.Float(string="En especie y dinero (Invalidez y vida)", compute="_compute_imss_fields", store=True)

    # Retiro, Cesantía en Edad Avanzada y Vejez
    cv = fields.Float(string="CV (Retiro, Cesantía y Vejez)", compute="_compute_imss_fields", store=True)

    # Total de indemnizaciones de IMSS
    total_imss = fields.Float(string="Total de indemnizaciones de IMSS", compute="_compute_imss_fields", store=True)

    @api.onchange('employee_id')
    def _onchange_employee_id_liq(self):
        if self.employee_id:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)
            self.contract_id = contract
        else:
            self.contract_id = False

    @api.depends('fecha_inicio', 'fecha_fin', 'salario')
    def _compute_fields_liq(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin:
                dias = (rec.fecha_fin - rec.fecha_inicio).days + 1
                dias = round(dias, 2)
                rec.dias_trabajados = dias
                anios_trabajados = round(dias / 365 if dias else 0.0, 2)
                rec.anios_trabajados = anios_trabajados
            else:
                rec.dias_trabajados = 0
                rec.anios_trabajados = 0.0
            salario_diario = round((rec.salario / 2) / 15 if rec.salario else 0.0, 2)
            rec.salario_diario = salario_diario

    @api.depends('fecha_fin', 'salario_diario', 'dias_aguinaldo')
    def _compute_aguinaldo_liq(self):
        from datetime import date
        for rec in self:
            if rec.fecha_fin:
                primer_dia = date(rec.fecha_fin.year, 1, 1)
                rec.primer_dia_ano = primer_dia
                dias_trab = (rec.fecha_fin - primer_dia).days + 1
                dias_trab = round(dias_trab, 2)
                rec.dias_trabajados_aguinaldo = dias_trab
                factor_aguinaldo = round(dias_trab / 365 if dias_trab else 0.0, 2)
                rec.factor_aguinaldo = factor_aguinaldo
                dias_que_corresponde = round(rec.dias_aguinaldo * factor_aguinaldo, 2)
                rec.dias_que_corresponde = dias_que_corresponde
                proporcional_aguinaldo = round(dias_que_corresponde * rec.salario_diario, 2)
                rec.proporcional_aguinaldo = proporcional_aguinaldo
            else:
                rec.primer_dia_ano = False
                rec.dias_trabajados_aguinaldo = 0
                rec.factor_aguinaldo = 0.0
                rec.dias_que_corresponde = 0.0
                rec.proporcional_aguinaldo = 0.0

    @api.depends('anios_trabajados', 'salario_diario')
    def _compute_vacaciones_liq(self):
        for rec in self:
            anios_trabajados = round(rec.anios_trabajados or 0.0, 2)
            anios_cumplidos = int(anios_trabajados)
            rec.anios_cumplidos = anios_cumplidos
            if anios_cumplidos <= 1:
                dias_vac = 12
            elif anios_cumplidos == 2:
                dias_vac = 14
            elif anios_cumplidos == 3:
                dias_vac = 16
            elif anios_cumplidos == 4:
                dias_vac = 18
            elif anios_cumplidos == 5:
                dias_vac = 20
            elif 6 <= anios_cumplidos <= 10:
                dias_vac = 22
            elif 11 <= anios_cumplidos <= 15:
                dias_vac = 24
            elif 16 <= anios_cumplidos <= 20:
                dias_vac = 26
            elif 21 <= anios_cumplidos <= 25:
                dias_vac = 28
            else:
                dias_vac = 0
            rec.dias_vacaciones = dias_vac
            factor_vac = round(anios_trabajados - anios_cumplidos if anios_trabajados else 0.0, 2)
            rec.factor_vacaciones = factor_vac
            dias_corresponde = round(factor_vac * dias_vac, 2)
            rec.dias_que_le_corresponde = dias_corresponde
            proporcional_vacaciones_sin_2022 = round(dias_corresponde * rec.salario_diario, 2)
            rec.proporcional_vacaciones_sin_2022 = proporcional_vacaciones_sin_2022

    @api.depends('proporcional_vacaciones_sin_2022', 'porcentaje_prima')
    def _compute_prima_vacacional_liq(self):
        for rec in self:
            porcentaje = round((rec.porcentaje_prima or 0) / 100.0, 2)
            rec.prima_vacacional = round(rec.proporcional_vacaciones_sin_2022 * porcentaje, 2)

    @api.depends('salario_diario', 'anios_cumplidos', 'anios_trabajados')
    def _compute_indemnizacion_liq(self):
        SALARIO_TOPADO_1 = 557.60
        for rec in self:
            salario_diario = round(rec.salario_diario or 0.0, 2)
            anios_cumplidos = round(rec.anios_cumplidos or 0, 2)
            anios_trabajados = round(rec.anios_trabajados or 0.0, 2)
            rec.indemnizacion = round(salario_diario * 30 * 3, 2)
            rec.veinte_dias_por_anio = round(20 * anios_cumplidos * salario_diario, 2)
            salario_topado = round(SALARIO_TOPADO_1, 2) if salario_diario > SALARIO_TOPADO_1 else salario_diario
            rec.prima_antiguedad = round(12 * anios_trabajados * salario_topado, 2)

    @api.depends('anios_trabajados')
    def _compute_impuestos_indemnizacion(self):
        MONTO_TOTAL_EXENTO = 10182.60  # UMA mensual X 90 umas de parte exenta
        for rec in self:
            rec.monto_exento_indemnizacion = round(MONTO_TOTAL_EXENTO * (rec.anios_trabajados or 0.0), 2)

    @api.depends('salario_diario')
    def _compute_isr_liquidacion(self):
        # Tabla ISR 2025 (no visible)
        TABLA_ISR = [
            {"lim_inf": 0.01, "lim_sup": 746.04, "cuota_fija": 0.00, "porcentaje": 1.92},
            {"lim_inf": 746.05, "lim_sup": 6332.05, "cuota_fija": 14.32, "porcentaje": 6.40},
            {"lim_inf": 6332.06, "lim_sup": 11128.01, "cuota_fija": 371.83, "porcentaje": 10.88},
            {"lim_inf": 11128.02, "lim_sup": 12935.82, "cuota_fija": 893.63, "porcentaje": 16.00},
            {"lim_inf": 12935.83, "lim_sup": 15487.71, "cuota_fija": 1182.88, "porcentaje": 17.92},
            {"lim_inf": 15487.72, "lim_sup": 31236.49, "cuota_fija": 1640.18, "porcentaje": 21.36},
            {"lim_inf": 31236.50, "lim_sup": 49233.00, "cuota_fija": 5004.12, "porcentaje": 23.52},
            {"lim_inf": 49233.01, "lim_sup": 93993.90, "cuota_fija": 9236.89, "porcentaje": 30.00},
            {"lim_inf": 93993.91, "lim_sup": 125325.20, "cuota_fija": 22665.17, "porcentaje": 32.00},
            {"lim_inf": 125325.21, "lim_sup": 375975.61, "cuota_fija": 32691.18, "porcentaje": 34.00},
            {"lim_inf": 375975.62, "lim_sup": float('inf'), "cuota_fija": 117912.32, "porcentaje": 35.00},
        ]
        for rec in self:
            salario_diario = round(rec.salario_diario or 0.0, 2)
            salario_mensual_ordinario = round(salario_diario * 30.4, 2)
            rec.salario_mensual_ordinario = salario_mensual_ordinario
            # Buscar el rango en la tabla
            fila = next((f for f in TABLA_ISR if f["lim_inf"] <= salario_mensual_ordinario <= f["lim_sup"]), None)
            if fila:
                lim_inf = round(fila["lim_inf"], 2)
                cuota_fija = round(fila["cuota_fija"], 2)
                porcentaje = round(fila["porcentaje"], 2)
                excedente1 = round(salario_mensual_ordinario - lim_inf, 2)
                rec.excedente1 = excedente1
                calculo_1 = round(excedente1 * (porcentaje / 100), 2)
                calculo_2 = round(cuota_fija + calculo_1, 2)
                rec.factor_conversion = round(calculo_2 / salario_mensual_ordinario, 4) if salario_mensual_ordinario else 0.0
            else:
                rec.excedente1  = 0.0
                rec.factor_conversion = 0.0

    @api.depends('salario_diario', 'monto_exento_indemnizacion', 'factor_conversion', 'indemnizacion')
    def _compute_isr_liquidacion_final(self):
        for rec in self:
            # Cálculo 3 (no visible)
            calculo_3 = round(90 * (rec.salario_diario or 0.0), 4)
            # Importe gravado
            importe_gravado = round(calculo_3 - (rec.monto_exento_indemnizacion or 0.0), 4)
            rec.importe_gravado = importe_gravado
            # Retención de ISR
            retencion_isr = round(importe_gravado * (rec.factor_conversion or 0.0), 4)
            rec.retencion_isr = retencion_isr
            # Total de Indemnización
            rec.total_indemnizacion = round((rec.indemnizacion or 0.0) - retencion_isr, 4)

    @api.depends('prima_antiguedad', 'monto_exento_indemnizacion', 'factor_conversion')
    def _compute_prima_antiguedad_liq(self):
        for rec in self:
            gravado = max((rec.prima_antiguedad or 0.0) - (rec.monto_exento_indemnizacion or 0.0), 0.0)
            rec.gravado_prima_antiguedad = round(gravado, 4)
            rec.retencion_prima_antiguedad = round(gravado * (rec.factor_conversion or 0.0), 4)
            rec.total_indemnizacion_prima_antiguedad = round((rec.prima_antiguedad or 0.0) - rec.retencion_prima_antiguedad, 4)

    @api.depends('veinte_dias_por_anio', 'monto_exento_indemnizacion', 'factor_conversion')
    def _compute_veinte_dias_impuestos(self):
        for rec in self:
            if (rec.veinte_dias_por_anio or 0.0) > (rec.monto_exento_indemnizacion or 0.0):
                gravamen = (rec.veinte_dias_por_anio or 0.0) - (rec.monto_exento_indemnizacion or 0.0)
            else:
                gravamen = 0.0
            rec.gravamen_veinte_dias = round(gravamen, 4)
            rec.retencion_veinte_dias = round(gravamen * (rec.factor_conversion or 0.0), 4)
            rec.total_indemnizacion_veinte_dias = round((rec.veinte_dias_por_anio or 0.0) - rec.retencion_veinte_dias, 4)

    @api.depends('fecha_fin', 'salario_diario')
    def _compute_salario_proporcional(self):
        from datetime import date
        for rec in self:
            if rec.fecha_fin and rec.salario_diario:
                # Determinar el día de corte (1 o 15 del mes)
                dia = rec.fecha_fin.day
                if dia > 15:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 15)
                else:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 1)
                dias = (rec.fecha_fin - corte).days + 1
                dias = dias if dias > 0 else 0
                rec.salario_proporcional = round(dias * rec.salario_diario, 2)
            else:
                rec.salario_proporcional = 0.0

    def action_descargar_liquidacion(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'hr_cardic.reporte_liquidacion_pdf_template',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'res_model': self._name,
        }

    @api.depends('dias_vacaciones', 'salario_diario', 'fecha_fin')
    def _compute_fi_sdi(self):
        from datetime import date
        for rec in self:
            # FI1 y FI2
            fi1 = 365 + 15 + ((rec.dias_vacaciones or 0) * 0.25)
            rec.fi1 = fi1
            fi2 = fi1 / 365
            rec.fi2 = fi2
            rec.sdi = round(fi2 * (rec.salario_diario or 0), 2)
            # Días trabajados a la quincena
            if rec.fecha_fin:
                dia = rec.fecha_fin.day
                if dia > 15:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 15)
                else:
                    corte = date(rec.fecha_fin.year, rec.fecha_fin.month, 1)
                dias = (rec.fecha_fin - corte).days + 1
                dias = dias if dias > 0 else 0
                rec.dias_trabajados_quincena = dias
            else:
                rec.dias_trabajados_quincena = 0

    @api.depends('sdi', 'dias_trabajados_quincena')
    def _compute_imss_fields(self):
        for rec in self:
            # Enfermedades y maternidad
            rec.en_especie = round(3 * 113.14, 2)
            rec.roimss = round((rec.sdi or 0) - rec.en_especie, 2)
            rec.excedente = round(rec.roimss * 0.004, 2)
            rec.gastos_medicos = round(0.00375 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            rec.en_dinero = round(0.0025 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Invalidez y vida
            rec.invalidez_vida = round(0.00625 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Retiro, Cesantía y Vejez
            rec.cv = round(0.01125 * (rec.sdi or 0) * (rec.dias_trabajados_quincena or 0), 2)
            # Total IMSS
            rec.total_imss = round((rec.excedente or 0) + (rec.gastos_medicos or 0) + (rec.en_dinero or 0) + (rec.invalidez_vida or 0) + (rec.cv or 0), 2)

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    caja_chica_id = fields.Many2one('hr_cardic.caja_chica', string='Caja Chica')
    ruta_id = fields.Many2one('hr_cardic.ruta', string='Ruta')

    # Opcional: sincronizar ruta automáticamente si se selecciona una caja chica
    @api.onchange('caja_chica_id')
    def _onchange_caja_chica_id(self):
        if self.caja_chica_id and self.caja_chica_id.ruta_ids:
            self.ruta_id = self.caja_chica_id.ruta_ids[0]
