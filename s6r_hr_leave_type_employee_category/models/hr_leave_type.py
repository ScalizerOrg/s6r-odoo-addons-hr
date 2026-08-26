# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.osv import expression


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
        return bool(self._filter_allowed_employees(employee))

    def _filter_allowed_employees(self, employees):
        """Return the employees among the given ones this time off type is open to.

        The batch counterpart of :meth:`_is_allowed_for_employee`, which is written on
        top of it so the two can never come to disagree. Reads the tags of the whole
        set in one go: a per-record ``sudo()`` costs a query an employee, and the batch
        generation wizards run this over a whole company.

        A type carrying no tag is open to everybody, so everybody comes back.

        :param employees: the employees to sort out
        :type employees: recordset hr.employee
        :returns: those the type is open to
        :rtype: recordset hr.employee
        """
        self.ensure_one()
        if not self.restricted_category_ids:
            return employees
        categories = self.restricted_category_ids
        # sudo: hr.employee.category_ids is reserved to the HR users, and this runs
        # both for the very employee requesting their own time off and for an officer
        # who is not necessarily one of them.
        allowed_ids = {
            employee.id
            for employee in employees.sudo()
            if categories & employee.category_ids
        }
        return employees.filtered(lambda employee: employee.id in allowed_ids)

    @api.model
    def _get_restriction_visibility_employee(self):
        """Return the employee the time off types must be filtered for, if any.

        Filters only when the context designates an employee, which is what tells a
        screen where somebody books from a screen where somebody administers. Falling
        back on the employee of the current user, the way ``_get_contextual_employee``
        does, would filter the configuration list against the tags of whoever opens it,
        and the user groups are no help telling the two apart: an employee holding a
        restricted tag is perfectly able to also hold the Time Off officer rights.

        The employee-facing entry points are served: both the time off form and the
        allocation form pass ``employee_id`` on the time off type field themselves
        (hr_holidays 18.0), and ``onchange`` puts it in the context of a record being
        filled in.

        :returns: the employee to filter for, empty when nothing must be filtered
        :rtype: recordset hr.employee
        """
        context = self.env.context
        if context.get("skip_leave_type_employee_filter"):
            return self.env["hr.employee"]
        explicit = context.get("employee_id") or context.get("default_employee_id")
        if not explicit:
            return self.env["hr.employee"]
        # sudo: reading the tags of the employee is out of reach of the very user
        # this filters for.
        return self.env["hr.employee"].sudo().browse(explicit).exists()

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Narrow the types down to the employee the context designates.

        Two restrictions, both keyed on that employee:

        * the tags: a type reserved to some is hidden from whoever holds none of them;
        * the company: the type of another company has no business being offered for an
          employee, the native record rule only ever checking the companies of the
          *user*, so a two-company officer is otherwise offered both.

        Filtering the search rather than narrowing the ``domain`` of the field on the
        form: the native domain of ``holiday_status_id`` is not ours to replace. On the
        allocation it lives on the field itself in Python
        (``hr.leave.allocation._domain_holiday_status_id``, the arch carrying none) and
        an arch domain would shadow it, offering an employee the types HR never opened
        to their requests. On the time off it would have to be copied over verbatim, to
        drift on the next migration, and any other module narrowing that same attribute
        would silently undo ours, or ours theirs.

        The constraint remains the lock on the tags; this only keeps the form from
        offering what it would refuse.

        :returns: the query of the matching types
        """
        employee = self._get_restriction_visibility_employee()
        if employee:
            # sudo: reading the tags and the company of the employee is out of reach
            # of the very user this filters for.
            employee = employee.sudo()
            restrictions = [[
                "|",
                ("restricted_category_ids", "=", False),
                ("restricted_category_ids", "in", employee.category_ids.ids),
            ]]
            if not self._domain_states_company(domain):
                restrictions.append(
                    [("company_id", "in", employee.company_id.ids + [False])]
                )
            domain = expression.AND([domain, *restrictions])
        return super()._search(domain, offset, limit, order)

    @api.model
    def _domain_states_company(self, domain):
        """Return whether a domain already says which company it wants types of.

        The company of the employee is only filled in for a caller that expressed
        nothing: one naming ``company_id`` itself knows which company it is after, and
        is not necessarily asking for the employee sitting in the context. The batch
        generation wizards do (their type field is scoped on their own company field),
        and so does any module looking a type up by company -- the SAFE overtime
        counters, whose lookups target a company that may not even be among the ones the
        user is allowed.

        :param domain: the domain the search was called with
        :type domain: list
        :returns: True when the domain constrains the company itself
        :rtype: bool
        """
        return any(
            isinstance(leaf, (list, tuple))
            and len(leaf) == 3
            and str(leaf[0]).split(".")[0] == "company_id"
            for leaf in domain
        )
