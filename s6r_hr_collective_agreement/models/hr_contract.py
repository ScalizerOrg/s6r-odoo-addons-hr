# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    hr_cba_id = fields.Many2one('hr.cba', string='CBA')
    hr_cba_position_id = fields.Many2one('hr.cba.position', string='CBA Position')
