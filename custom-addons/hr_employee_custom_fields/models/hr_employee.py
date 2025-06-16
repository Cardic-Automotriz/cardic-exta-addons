from odoo import models, fields, api
from datetime import date, timedelta
import calendar

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee Custom Fields'

    # Permisos de acceso
    _sql_constraints = [
        ('rfc_uniq', 'unique(rfc)', 'El RFC debe ser único!'),
        ('nss_uniq', 'unique(nss)', 'El NSS debe ser único!'),
        ('curp_uniq', 'unique(curp)', 'El CURP debe ser único!'),
    ]

    # currency_id para el campo Monetary
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id)

    # Campos relacionados con el contrato
    contract_id = fields.Many2one('hr.contract', string="Contrato", tracking=True)
    contract_date_start = fields.Date(related='contract_id.date_start', string="Fecha Inicio Contrato", store=True, tracking=True)
    salario = fields.Monetary(related='contract_id.wage', string="Salario", currency_field='currency_id', store=True, tracking=True)

    salario_diario = fields.Float(string='Salario Diario', compute='_compute_salario_diario', digits=(16,4), store=True)
    fecha_corte = fields.Date(string='Fecha de Corte', compute='_compute_fecha_corte', store=True)
    dias_trabajados = fields.Float(string='Días Trabajados', compute='_compute_dias_trabajados', digits=(16,4), store=True)
    anios_trabajados = fields.Float(string='Años Trabajados', compute='_compute_anios_trabajados', digits=(16,4), store=True)
    anios_cumplidos = fields.Integer(string='Años Cumplidos', compute='_compute_anios_cumplidos', store=True)
    vacaciones = fields.Float(string='Vacaciones', compute='_compute_vacaciones', digits=(16,4), store=True)
    sdi = fields.Float(string='SDI', compute='_compute_sdi', digits=(16,4), store=True)
    faltas = fields.Float(string='Faltas', default=0.0)
    sueldo = fields.Float(string='Sueldo', compute='_compute_sueldo', digits=(16,4), store=True)

    @api.depends('salario')
    def _compute_salario_diario(self):
        for rec in self:
            rec.salario_diario = round(rec.salario / 30.0, 4) if rec.salario else 0.0

    @api.depends('contract_date_start')
    def _compute_fecha_corte(self):
        for rec in self:
            today = date.today()
            # Próximo 15 o fin de mes
            if today.day <= 15:
                corte = today.replace(day=15)
            else:
                last_day = calendar.monthrange(today.year, today.month)[1]
                corte = today.replace(day=last_day)
            rec.fecha_corte = corte

    @api.depends('contract_date_start', 'fecha_corte')
    def _compute_dias_trabajados(self):
        for rec in self:
            if rec.contract_date_start and rec.fecha_corte:
                rec.dias_trabajados = round((rec.fecha_corte - rec.contract_date_start).days, 4)
            else:
                rec.dias_trabajados = 0.0

    @api.depends('dias_trabajados')
    def _compute_anios_trabajados(self):
        for rec in self:
            rec.anios_trabajados = round(rec.dias_trabajados / 365.0, 4) if rec.dias_trabajados else 0.0

    @api.depends('anios_trabajados')
    def _compute_anios_cumplidos(self):
        for rec in self:
            rec.anios_cumplidos = int(rec.anios_trabajados)

    @api.depends('anios_cumplidos')
    def _compute_vacaciones(self):
        for rec in self:
            anios = rec.anios_cumplidos
            if anios < 1:
                rec.vacaciones = 12.0
            elif anios == 1:
                rec.vacaciones = 12.0
            elif anios == 2:
                rec.vacaciones = 14.0
            elif anios == 3:
                rec.vacaciones = 16.0
            elif anios == 4:
                rec.vacaciones = 18.0
            elif anios == 5:
                rec.vacaciones = 20.0
            elif 6 <= anios <= 10:
                rec.vacaciones = 22.0
            elif 11 <= anios <= 15:
                rec.vacaciones = 24.0
            else:
                # A partir de 16 años, cada 5 años +2 días
                rec.vacaciones = 24.0 + 2.0 * ((anios - 11) // 5 + 1)

    @api.depends('salario_diario', 'vacaciones')
    def _compute_sdi(self):
        for rec in self:
            try:
                rec.sdi = round(((365 + 15 + (rec.vacaciones / 0.25)) / 365) * rec.salario_diario, 4) if rec.salario_diario else 0.0
            except Exception:
                rec.sdi = 0.0

    @api.depends('salario_diario', 'faltas')
    def _compute_sueldo(self):
        for rec in self:
            try:
                rec.sueldo = round((15.0 - rec.faltas) * rec.salario_diario, 4) if rec.salario_diario is not None and rec.faltas is not None else 0.0
            except Exception:
                rec.sueldo = 0.0 