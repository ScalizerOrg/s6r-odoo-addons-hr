# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class HrLeaveCategoryRestrictionMixin(models.AbstractModel):
    """Time off type restriction by employee tag, shared by time off and allocations.

    Both models carry the same two fields (``employee_id`` and
    ``holiday_status_id``) and owe the user the same behaviour: only offer the
    types their tags entitle them to, and refuse the others server-side.

    The offering itself is not done here: it belongs to
    ``hr.leave.type._search``, which both forms reach through the ``employee_id``
    they already put in the context of the type field.
    """

    _name = "hr.leave.category.restriction.mixin"
    _description = "Time Off Type Restriction by Employee Tag"

    @api.model
    def _drop_unallowed_default_type(self, defaults):
        """Drop a default time off type the employee is not offered.

        The core fills the field in by taking the first type its own search returns
        (``hr.leave.default_get``, ``hr.leave.allocation._default_holiday_status_id``).
        That search is filtered by ``hr.leave.type._search`` whenever the context
        designates an employee, but the plain *New* of the Time Off list carries no such
        context: the core resolves the employee afterwards, and the form would open on a
        type the employee is not entitled to, absent from the very list it offers next to
        it.

        Called by the ``default_get`` of the models rather than carried by this mixin: the
        core reaches the mixin through its own ``super()`` call, hence before it picks the
        type, and the value has to be judged once it is picked.

        The type is probed with the employee in the context rather than checked against
        the tags alone, so a type another module hides for that employee goes too. Nothing
        is substituted: the field is required, and the list next to it is right.

        :param dict defaults: the default values the core computed
        :returns: the same values, without a type the employee may not use
        :rtype: dict
        """
        if not defaults.get("holiday_status_id"):
            return defaults
        employee = self._get_restriction_employee(defaults)
        if not employee:
            return defaults
        LeaveType = self.env["hr.leave.type"].with_context(employee_id=employee.id)
        if LeaveType.search([("id", "=", defaults["holiday_status_id"])]):
            return defaults
        defaults["holiday_status_id"] = False
        return defaults

    @api.model
    def _get_restriction_employee(self, defaults):
        """Return the employee the defaults are being built for.

        :param dict defaults: the default values computed so far
        :returns: the employee, empty when none can be resolved
        :rtype: recordset hr.employee
        """
        context = self.env.context
        employee_id = (
            defaults.get("employee_id")
            or context.get("default_employee_id")
            or context.get("employee_id")
        )
        if employee_id:
            # sudo: resolving the employee of a request is out of reach of the very
            # user filing it.
            return self.env["hr.employee"].sudo().browse(employee_id).exists()
        return self.env.user.employee_id.sudo()

    @api.constrains("employee_id", "holiday_status_id")
    def _check_leave_type_category(self):
        """Refuse a type reserved to tags the employee does not hold.

        The real lock, the filtering of the form being only a convenience: an import,
        a custom wizard or another module goes through this constraint just the
        same.

        :raises ValidationError: when the employee holds none of the required tags
        :returns: None
        """
        for record in self:
            leave_type = record.holiday_status_id
            if not leave_type or not record.employee_id:
                continue
            if leave_type._is_allowed_for_employee(record.employee_id):
                continue
            raise ValidationError(
                _(
                    "%(employee)s does not hold any of the employee tags the time "
                    "off type \"%(leave_type)s\" is reserved to (%(tags)s).",
                    employee=record.employee_id.name,
                    leave_type=leave_type.display_name,
                    tags=", ".join(
                        leave_type.restricted_category_ids.mapped("name")
                    ),
                )
            )
