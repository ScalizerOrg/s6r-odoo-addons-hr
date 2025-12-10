# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrCbaPosition(models.Model):
    _name = 'hr.cba.position'
    _description = 'HR CBA (Collective Bargaining Agreement) Position'

    hr_cba_id = fields.Many2one('hr.cba', string='CBA', required=True)
    position = fields.Char(required=True)
    coefficient = fields.Float()
    maximum_first_trial_period = fields.Integer(compute='_compute_maximum_first_trial_period', readonly=False)
    maximum_trial_period = fields.Integer(compute='_compute_maximum_trial_period', readonly=False)
    maximum_first_trial_period_month = fields.Integer()
    maximum_trial_period_month = fields.Integer()
    display_name = fields.Char(compute='_compute_display_name', store=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.position} - {rec.coefficient}"

    @api.depends('maximum_first_trial_period_month')
    def _compute_maximum_first_trial_period(self):
        for rec in self:
            rec.maximum_first_trial_period = rec.maximum_first_trial_period_month * 30

    @api.depends('maximum_trial_period_month')
    def _compute_maximum_trial_period(self):
        for rec in self:
            rec.maximum_trial_period = rec.maximum_trial_period_month * 30

    @api.onchange('maximum_first_trial_period')
    def _onchange_maximum_first_trial_period(self):
        for rec in self:
            rec.maximum_first_trial_period_month = rec.maximum_first_trial_period / 30

    @api.onchange('maximum_trial_period')
    def _onchange_maximum_trial_period(self):
        for rec in self:
            rec.maximum_trial_period_month = rec.maximum_trial_period / 30
