# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class HrLeaveType(models.Model):
    """Extension of hr.leave.type to flag HR-manager-only leave types."""

    _inherit = "hr.leave.type"

    hr_only = fields.Boolean(
        string="HR Only",
        default=False,
        help=(
            "When enabled, this leave type is reserved for HR managers only "
            "and will not appear in the employee leave request form."
        ),
    )
