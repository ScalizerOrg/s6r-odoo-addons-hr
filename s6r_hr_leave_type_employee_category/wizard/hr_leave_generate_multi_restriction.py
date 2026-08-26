# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, models
from odoo.exceptions import UserError

# Beyond that, the dialog turns into a wall of names nobody reads. The total is
# stated whatever happens, so nothing is silently swallowed.
MAX_LISTED_EMPLOYEES = 10


class HrLeaveGenerateMultiRestrictionMixin(models.AbstractModel):
    """Employee tag restriction on the batch generation wizards.

    Both wizards of hr_holidays 18.0, time off and allocation, pick the time off type
    first and the employees second, through one and the same
    ``_get_employees_from_allocation_mode``. The restriction is therefore applied to the
    employees: the type field of those two screens is deliberately left whole, an
    officer configuring a batch there rather than booking for themselves.

    Without this, the constraint fires on the first offending employee of the batch,
    rolls the whole generation back, and names that one employee out of a company.

    Only the sorting out lives here, the ``_get_employees_from_allocation_mode`` of each
    wizard calling it: carried by this mixin, it would be shadowed by the method of the
    core class, which comes first in the MRO of a model extended through ``_inherit``.
    """

    _name = "hr.leave.generate.multi.restriction.mixin"
    _description = "Employee Tag Restriction on the Batch Generation Wizards"

    def _filter_restricted_employees(self, employees):
        """Keep the employees the chosen time off type is open to.

        Named employees and a population are not the same request:

        * *By Employee* is a list typed in one by one. Dropping one of them silently
          would hide a mistake, so it raises, naming every employee at fault rather
          than the first one the constraint would have tripped on.
        * *By Company*, *By Department* and *By Employee Tag* designate a population, of
          which a restricted type only ever concerns a part: the others are dropped,
          which is the whole point of the restriction. It only raises when the
          restriction leaves nobody at all, a generation over an empty set being a
          silent no-op otherwise.

        :param employees: the employees the allocation mode designated
        :type employees: recordset hr.employee
        :raises UserError: on named employees the type is not open to, or when the
            restriction leaves nobody to generate for
        :returns: the employees the generation must run on
        :rtype: recordset hr.employee
        """
        self.ensure_one()
        leave_type = self.holiday_status_id
        if not employees or not leave_type.restricted_category_ids:
            return employees
        allowed = leave_type._filter_allowed_employees(employees)
        refused = employees - allowed
        if not refused:
            return employees
        if self.allocation_mode == "employee":
            raise UserError(
                _(
                    "The time off type \"%(leave_type)s\" is reserved to the employee "
                    "tags %(tags)s. %(count)s of the selected employees hold none of "
                    "them: %(employees)s",
                    leave_type=leave_type.display_name,
                    tags=self._format_restricted_tags(leave_type),
                    count=len(refused),
                    employees=self._format_employee_names(refused),
                )
            )
        if not allowed:
            raise UserError(
                _(
                    "None of the %(count)s employees selected holds any of the employee "
                    "tags the time off type \"%(leave_type)s\" is reserved to "
                    "(%(tags)s): there is nothing to generate.",
                    count=len(employees),
                    leave_type=leave_type.display_name,
                    tags=self._format_restricted_tags(leave_type),
                )
            )
        return allowed

    def _format_restricted_tags(self, leave_type):
        """Return the tags a time off type is reserved to, for a message.

        :param leave_type: the time off type
        :type leave_type: recordset hr.leave.type
        :returns: the tag names, comma separated
        :rtype: str
        """
        return ", ".join(leave_type.restricted_category_ids.mapped("name"))

    def _format_employee_names(self, employees):
        """Return the names of the employees for a message, the long lists cut short.

        :param employees: the employees to name
        :type employees: recordset hr.employee
        :returns: the names, comma separated, with the count of those left out
        :rtype: str
        """
        names = ", ".join(employees[:MAX_LISTED_EMPLOYEES].mapped("name"))
        left_out = len(employees) - MAX_LISTED_EMPLOYEES
        if left_out > 0:
            return _("%(names)s and %(count)s others", names=names, count=left_out)
        return names
