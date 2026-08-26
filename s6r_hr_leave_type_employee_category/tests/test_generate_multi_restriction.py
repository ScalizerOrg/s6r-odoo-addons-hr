# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestGenerateMultiRestriction(TransactionCase):
    """The batch generation wizards against a type reserved to employee tags.

    Left alone, the constraint fires on the first offending employee of the batch,
    rolls the whole generation back and names that one employee out of a company.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["hr.employee.category"]
        cls.tag_tech = Category.create({"name": "Batch Technician Test Tag"})
        cls.company = cls.env.company
        cls.department = cls.env["hr.department"].create(
            {"name": "Batch Restriction Test Department", "company_id": cls.company.id}
        )
        cls.tagged, cls.untagged = (
            cls.env["hr.employee"]
            .create(
                [
                    {
                        "name": "Batch Tagged Employee Test",
                        "company_id": cls.company.id,
                        "department_id": cls.department.id,
                        "category_ids": [Command.set(cls.tag_tech.ids)],
                    },
                    {
                        "name": "Batch Untagged Employee Test",
                        "company_id": cls.company.id,
                        "department_id": cls.department.id,
                    },
                ]
            )
        )
        cls.restricted_type = cls.env["hr.leave.type"].create(
            {
                "name": "Batch Technician Only Leave Test",
                "restricted_category_ids": [Command.set(cls.tag_tech.ids)],
                "leave_validation_type": "no_validation",
                "requires_allocation": "no",
                "company_id": cls.company.id,
            }
        )

    @staticmethod
    def _next_monday():
        """Return a working day the batch generation actually books days on.

        The wizard drops the employees the period holds no working day for, so a date
        landing on a week-end would empty the batch whatever the tags say.

        :returns: the first Monday in more than a week
        :rtype: date
        """
        day = fields.Date.today() + timedelta(days=8)
        return day + timedelta(days=-day.weekday() % 7)

    def _leave_wizard(self, **vals):
        """Return a batch time off wizard on the restricted type.

        :returns: recordset hr.leave.generate.multi.wizard
        """
        date_from = self._next_monday()
        return self.env["hr.leave.generate.multi.wizard"].create(
            {
                "name": "Batch Restriction Test",
                "holiday_status_id": self.restricted_type.id,
                "company_id": self.company.id,
                "date_from": date_from,
                "date_to": date_from,
                **vals,
            }
        )

    def _allocation_wizard(self, **vals):
        """Return a batch allocation wizard on the restricted type.

        :returns: recordset hr.leave.allocation.generate.multi.wizard
        """
        return self.env["hr.leave.allocation.generate.multi.wizard"].create(
            {
                "holiday_status_id": self.restricted_type.id,
                "company_id": self.company.id,
                "duration": 1,
                "date_from": fields.Date.today(),
                **vals,
            }
        )

    # ─── Named employees: it raises rather than dropping one ──────────────────
    def test_named_employees_refused_when_one_holds_no_tag(self):
        """A named employee the type is not open to stops the batch, and says who.

        The employees were typed in one by one: dropping one silently would hide a
        mistake.
        """
        wizard = self._leave_wizard(
            allocation_mode="employee",
            employee_ids=[Command.set((self.tagged | self.untagged).ids)],
        )
        with self.assertRaises(UserError) as caught:
            wizard.action_generate_time_off()
        message = str(caught.exception)
        self.assertIn(self.untagged.name, message, "the employee at fault is named")
        self.assertNotIn(self.tagged.name, message, "the entitled one is not")
        self.assertIn(self.tag_tech.name, message, "the required tag is named")
        self.assertFalse(
            self.env["hr.leave"].search_count(
                [("holiday_status_id", "=", self.restricted_type.id)]
            ),
            "nothing is generated",
        )

    def test_named_employees_generated_when_all_hold_the_tag(self):
        """Named employees the type is open to go through untouched."""
        wizard = self._leave_wizard(
            allocation_mode="employee",
            employee_ids=[Command.set(self.tagged.ids)],
        )
        wizard.action_generate_time_off()
        self.assertEqual(
            self.env["hr.leave"].search_count(
                [
                    ("holiday_status_id", "=", self.restricted_type.id),
                    ("employee_id", "=", self.tagged.id),
                ]
            ),
            1,
        )

    def test_named_employees_allocation_refused(self):
        """The allocation wizard behaves the same on named employees."""
        wizard = self._allocation_wizard(
            allocation_mode="employee",
            employee_ids=[Command.set((self.tagged | self.untagged).ids)],
        )
        with self.assertRaises(UserError):
            wizard.action_generate_allocations()

    # ─── A population: the employees at fault are dropped ────────────────────
    def test_department_keeps_only_the_entitled_employees(self):
        """A department is a population, of which the type only concerns a part."""
        wizard = self._leave_wizard(
            allocation_mode="department", department_id=self.department.id
        )
        wizard.action_generate_time_off()
        leaves = self.env["hr.leave"].search(
            [("holiday_status_id", "=", self.restricted_type.id)]
        )
        self.assertEqual(leaves.employee_id, self.tagged)

    def test_department_allocation_keeps_only_the_entitled_employees(self):
        """The allocation wizard drops the same way on a population."""
        wizard = self._allocation_wizard(
            allocation_mode="department", department_id=self.department.id
        )
        wizard.action_generate_allocations()
        allocations = self.env["hr.leave.allocation"].search(
            [("holiday_status_id", "=", self.restricted_type.id)]
        )
        self.assertEqual(allocations.employee_id, self.tagged)

    def test_population_leaving_nobody_is_refused(self):
        """A population the type is open to nobody of is a silent no-op otherwise."""
        self.tagged.category_ids = [Command.clear()]
        wizard = self._leave_wizard(
            allocation_mode="department", department_id=self.department.id
        )
        with self.assertRaises(UserError) as caught:
            wizard.action_generate_time_off()
        self.assertIn(self.tag_tech.name, str(caught.exception))

    def test_unrestricted_type_touches_nothing(self):
        """A type carrying no tag generates for the whole population."""
        open_type = self.env["hr.leave.type"].create(
            {
                "name": "Batch Open Leave Test",
                "leave_validation_type": "no_validation",
                "requires_allocation": "no",
                "company_id": self.company.id,
            }
        )
        wizard = self._leave_wizard(
            holiday_status_id=open_type.id,
            allocation_mode="department",
            department_id=self.department.id,
        )
        wizard.action_generate_time_off()
        leaves = self.env["hr.leave"].search(
            [("holiday_status_id", "=", open_type.id)]
        )
        self.assertEqual(leaves.employee_id, self.tagged | self.untagged)

    def test_long_refused_list_is_cut_short_but_counted(self):
        """A wall of names is cut short, the total being stated whatever happens."""
        from odoo.addons.s6r_hr_leave_type_employee_category.wizard import (
            hr_leave_generate_multi_restriction as restriction,
        )

        extra = self.env["hr.employee"].create(
            [
                {"name": "Batch Crowd Employee Test %s" % index, "company_id": self.company.id}
                for index in range(restriction.MAX_LISTED_EMPLOYEES + 3)
            ]
        )
        wizard = self._leave_wizard(
            allocation_mode="employee", employee_ids=[Command.set(extra.ids)]
        )
        with self.assertRaises(UserError) as caught:
            wizard.action_generate_time_off()
        message = str(caught.exception)
        self.assertIn(str(len(extra)), message, "the total is stated")
        self.assertIn("3 others", message, "the tail is counted, not dropped")
