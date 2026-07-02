# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrLeaveOnlyHr(TransactionCase):
    """Tests for the HR-only leave type restriction on hr.leave."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        hr_holidays_user = cls.env.ref("hr_holidays.group_hr_holidays_user")
        hr_holidays_manager = cls.env.ref("hr_holidays.group_hr_holidays_manager")

        cls.employee_user = cls.env["res.users"].create(
            {
                "name": "Regular Employee Test",
                "login": "s6r_only_hr_regular_employee_test",
                "groups_id": [(6, 0, [hr_holidays_user.id])],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Regular Employee Test",
                "user_id": cls.employee_user.id,
            }
        )

        cls.hr_user = cls.env["res.users"].create(
            {
                "name": "HR Manager Test",
                "login": "s6r_only_hr_hr_manager_test",
                "groups_id": [(6, 0, [hr_holidays_manager.id])],
            }
        )
        cls.hr_employee = cls.env["hr.employee"].create(
            {
                "name": "HR Manager Test",
                "user_id": cls.hr_user.id,
            }
        )

        cls.hr_only_type = cls.env["hr.leave.type"].create(
            {
                "name": "HR Only Leave Test",
                "hr_only": True,
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )

    def _leave_vals(self, employee, leave_type, date_from):
        """Return minimal vals for an hr.leave record."""
        date_from_date = date_from.date()
        return {
            "holiday_status_id": leave_type.id,
            "employee_id": employee.id,
            "request_date_from": date_from_date,
            "request_date_to": date_from_date + timedelta(days=1),
        }

    def test_hr_only_type_blocks_non_hr_user(self):
        """Non-HR user cannot create a leave with an HR-only type."""
        date_from = fields.Datetime.now() + timedelta(days=5)
        vals = self._leave_vals(self.employee, self.hr_only_type, date_from)
        with self.assertRaises(ValidationError):
            self.env["hr.leave"].with_user(self.employee_user).create(vals)

    def test_hr_only_type_allows_hr_user(self):
        """HR manager can create a leave with an HR-only type without error."""
        date_from = fields.Datetime.now() + timedelta(days=5)
        vals = self._leave_vals(self.hr_employee, self.hr_only_type, date_from)
        leave = self.env["hr.leave"].with_user(self.hr_user).create(vals)
        self.assertTrue(leave)
