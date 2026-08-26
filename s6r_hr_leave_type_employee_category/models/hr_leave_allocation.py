# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, models


class HrLeaveAllocation(models.Model):
    """Extension of hr.leave.allocation restricting the types to the employee tags."""

    _name = "hr.leave.allocation"
    _inherit = ["hr.leave.allocation", "hr.leave.category.restriction.mixin"]

    @api.model
    def default_get(self, fields_list):
        """Drop the default type when the employee may not use it.

        Post-processing rather than a plain override of the mixin: the core reaches the
        mixin through its own ``super()`` call, so the type it picks has to be judged
        after the fact.

        :param fields_list: names of the fields the defaults are asked for
        :returns: dict of default values
        """
        return self._drop_unallowed_default_type(super().default_get(fields_list))
