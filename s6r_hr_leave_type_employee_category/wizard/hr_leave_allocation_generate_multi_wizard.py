# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models


class HrLeaveAllocationGenerateMultiWizard(models.TransientModel):
    """Batch allocation generation, restricted to the tags of the chosen type."""

    _name = "hr.leave.allocation.generate.multi.wizard"
    _inherit = [
        "hr.leave.allocation.generate.multi.wizard",
        "hr.leave.generate.multi.restriction.mixin",
    ]

    def _get_employees_from_allocation_mode(self):
        """Drop, or refuse, the employees the chosen type is not open to.

        Declared here rather than on the mixin: the method of the core class comes
        first in the MRO of a model extended through ``_inherit``, so a mixin carrying
        it would never be reached.

        :returns: the employees the generation must run on
        :rtype: recordset hr.employee
        """
        return self._filter_restricted_employees(
            super()._get_employees_from_allocation_mode()
        )
