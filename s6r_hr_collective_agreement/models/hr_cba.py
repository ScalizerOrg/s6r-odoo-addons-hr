# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrCba(models.Model):
    _name = 'hr.cba'
    _description = 'HR CBA (Collective Bargaining Agreement)'

    name = fields.Char(required=True)
