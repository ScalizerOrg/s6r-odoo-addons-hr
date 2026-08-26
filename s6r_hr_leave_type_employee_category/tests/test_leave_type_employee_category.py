# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestLeaveTypeEmployeeCategory(TransactionCase):
    """Tests for the time off type restriction by employee tag."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tag_tech = cls.env["hr.employee.category"].create(
            {"name": "Technician Test Tag"}
        )
        cls.tag_support = cls.env["hr.employee.category"].create(
            {"name": "Support Test Tag"}
        )

        cls.tagged_employee = cls.env["hr.employee"].create(
            {
                "name": "Tagged Employee Test",
                "category_ids": [(6, 0, [cls.tag_tech.id])],
            }
        )
        cls.other_employee = cls.env["hr.employee"].create(
            {
                "name": "Other Employee Test",
                "category_ids": [(6, 0, [cls.tag_support.id])],
            }
        )
        cls.untagged_employee = cls.env["hr.employee"].create(
            {"name": "Untagged Employee Test"}
        )

        cls.restricted_type = cls.env["hr.leave.type"].create(
            {
                "name": "Technician Only Leave Test",
                "restricted_category_ids": [(6, 0, [cls.tag_tech.id])],
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )
        cls.open_type = cls.env["hr.leave.type"].create(
            {
                "name": "Open Leave Test",
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )

    def _leave_vals(self, employee, leave_type):
        """Return minimal vals for an hr.leave record.

        :returns: dict of values
        """
        date_from = (fields.Datetime.now() + timedelta(days=5)).date()
        return {
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "request_date_from": date_from,
            "request_date_to": date_from + timedelta(days=1),
        }

    def _allocation_vals(self, employee, leave_type):
        """Return minimal vals for an hr.leave.allocation record.

        :returns: dict of values
        """
        return {
            "name": "Allocation Test",
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "number_of_days": 1,
        }

    # ─── Type level predicate ────────────────────────────────────────────────
    def test_type_without_tag_is_open(self):
        """A type carrying no tag is allowed for anybody."""
        self.assertTrue(self.open_type._is_allowed_for_employee(self.untagged_employee))

    def test_type_allowed_on_matching_tag(self):
        """A restricted type is allowed for an employee holding one of its tags."""
        self.assertTrue(
            self.restricted_type._is_allowed_for_employee(self.tagged_employee)
        )

    def test_type_refused_on_other_tag(self):
        """A restricted type is refused for an employee holding another tag."""
        self.assertFalse(
            self.restricted_type._is_allowed_for_employee(self.other_employee)
        )
        self.assertFalse(
            self.restricted_type._is_allowed_for_employee(self.untagged_employee)
        )

    def test_type_allowed_without_employee(self):
        """With no employee to compare against, the type stays allowed.

        A time off requested for a whole department or company holds no employee
        of its own: the check belongs to the records created per employee.
        """
        self.assertTrue(
            self.restricted_type._is_allowed_for_employee(self.env["hr.employee"])
        )

    # ─── Allowed types driving the form domain ───────────────────────────────
    @staticmethod
    def _allowed_ids(record):
        """Return the ids of the types a record gives access to.

        Read through ``_origin``: on a record built with ``new()`` — what an unsaved
        form is — the value comes back as new records pointing at the real ones.

        :returns: list of hr.leave.type ids
        """
        return record.allowed_holiday_status_ids._origin.ids

    def test_allowed_types_on_leave(self):
        """The allowed types of a time off follow the tags of its employee."""
        leave = self.env["hr.leave"].new(
            self._leave_vals(self.tagged_employee, self.open_type)
        )
        self.assertIn(self.restricted_type.id, self._allowed_ids(leave))
        self.assertIn(self.open_type.id, self._allowed_ids(leave))

        leave = self.env["hr.leave"].new(
            self._leave_vals(self.other_employee, self.open_type)
        )
        self.assertNotIn(self.restricted_type.id, self._allowed_ids(leave))
        self.assertIn(self.open_type.id, self._allowed_ids(leave))

    def test_allowed_types_on_allocation(self):
        """The allowed types of an allocation follow the tags of its employee."""
        allocation = self.env["hr.leave.allocation"].new(
            self._allocation_vals(self.other_employee, self.open_type)
        )
        self.assertNotIn(self.restricted_type.id, self._allowed_ids(allocation))
        self.assertIn(self.open_type.id, self._allowed_ids(allocation))

    # ─── Server side constraint ──────────────────────────────────────────────
    def test_leave_refused_without_tag(self):
        """A time off on a restricted type is refused without the required tag."""
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                self._leave_vals(self.other_employee, self.restricted_type)
            )

    def test_leave_allowed_with_tag(self):
        """A time off on a restricted type goes through with the required tag."""
        leave = self.env["hr.leave"].create(
            self._leave_vals(self.tagged_employee, self.restricted_type)
        )
        self.assertTrue(leave)

    def test_allocation_refused_without_tag(self):
        """An allocation on a restricted type is refused without the required tag."""
        with self.assertRaises(ValidationError):
            self.env["hr.leave.allocation"].create(
                self._allocation_vals(self.untagged_employee, self.restricted_type)
            )

    def test_allocation_allowed_with_tag(self):
        """An allocation on a restricted type goes through with the required tag."""
        allocation = self.env["hr.leave.allocation"].create(
            self._allocation_vals(self.tagged_employee, self.restricted_type)
        )
        self.assertTrue(allocation)

    def test_allocation_write_refused_without_tag(self):
        """The constraint fires on write too, not only on create."""
        allocation = self.env["hr.leave.allocation"].create(
            self._allocation_vals(self.other_employee, self.open_type)
        )
        with self.assertRaises(ValidationError):
            allocation.write({"holiday_status_id": self.restricted_type.id})

    def test_allowed_types_do_not_leak_across_companies(self):
        """A wider company context does not leak its types into a narrower one.

        The core recomputes fields of a time off in a ``with_company(employee_company_id)``
        environment, which *adds* the company of the employee to the active ones. Were the
        compute not declared context dependent, the ORM would cache that one value for every
        context: the form would offer a type of a company that is not active, and reading it
        back raises an access error on the multi-company record rule.
        """
        Company = self.env["res.company"]
        other_company = Company.search([("id", "!=", self.env.company.id)], limit=1)
        if not other_company:
            other_company = Company.create({"name": "Other Restriction Test Co"})
        company_type = self.env["hr.leave.type"].create(
            {
                "name": "Other Company Leave Test",
                "company_id": other_company.id,
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Other Company Employee Test",
                "company_id": other_company.id,
            }
        )
        # Not as the superuser, who bypasses the record rules the leak trips on.
        user = self.env.ref("base.user_admin")
        user.company_ids = [Command.link(other_company.id)]
        leave = (
            self.env["hr.leave"]
            .with_user(user)
            .with_context(allowed_company_ids=[self.env.company.id])
            .new({"employee_id": employee.id})
        )
        # Warms the cache the way the core does, in the company of the employee.
        self.assertIn(
            company_type.id, self._allowed_ids(leave.with_company(other_company))
        )
        self.assertNotIn(company_type.id, self._allowed_ids(leave))

    # ─── Default value of the type field ─────────────────────────────────────
    def _make_restricted_type_the_core_default(self):
        """Put the restricted type first in the search the core defaults on.

        :returns: None
        """
        self.restricted_type.sequence = -100
        first = self.env["hr.leave.type"].search(
            ["|", ("requires_allocation", "=", "no"), ("has_valid_allocation", "=", True)],
            limit=1,
            order="sequence",
        )
        self.assertEqual(
            first, self.restricted_type, "the core would not default on the restricted type"
        )

    def test_default_type_dropped_when_not_entitled(self):
        """The core default is cleared when the employee holds none of the tags.

        Left alone, the form opens on a type absent from the list it offers.
        """
        self._make_restricted_type_the_core_default()
        defaults = (
            self.env["hr.leave"]
            .with_context(default_employee_id=self.other_employee.id)
            .default_get(["holiday_status_id", "employee_id"])
        )
        self.assertFalse(defaults.get("holiday_status_id"))

    def test_default_type_kept_when_entitled(self):
        """The core default survives for an employee holding one of the tags."""
        self._make_restricted_type_the_core_default()
        defaults = (
            self.env["hr.leave"]
            .with_context(default_employee_id=self.tagged_employee.id)
            .default_get(["holiday_status_id", "employee_id"])
        )
        self.assertEqual(defaults.get("holiday_status_id"), self.restricted_type.id)
