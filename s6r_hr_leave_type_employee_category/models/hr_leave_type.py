# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class HrLeaveType(models.Model):
    """Extension of hr.leave.type to reserve a type to some employee tags."""

    _inherit = "hr.leave.type"

    restricted_category_ids = fields.Many2many(
        "hr.employee.category",
        "hr_leave_type_employee_category_rel",
        "leave_type_id",
        "category_id",
        string="Restricted to Tags",
        help=(
            "Employee tags allowed to use this time off type. An employee holding "
            "at least one of them may request it; the others may not. Leave empty "
            "for no restriction at all."
        ),
    )

    def _is_allowed_for_employee(self, employee):
        """Return whether this time off type may be used for the given employee.

        A type carrying no tag is open to everybody. An employee holding at least
        one of the tags of the type is entitled to it, the others are not.

        No employee to check against (a time off requested for a whole department
        or company, where the children records carry the employee) leaves the type
        allowed: there is nothing to compare its tags with yet.

        :param employee: employee the time off or the allocation is for
        :type employee: recordset hr.employee
        :returns: True when the crossing is allowed
        :rtype: bool
        """
        self.ensure_one()
        if not self.restricted_category_ids or not employee:
            return True
        # sudo: hr.employee.category_ids is reserved to the HR users, and this runs
        # for the very employee requesting their own time off.
        return bool(self.restricted_category_ids & employee.sudo().category_ids)
