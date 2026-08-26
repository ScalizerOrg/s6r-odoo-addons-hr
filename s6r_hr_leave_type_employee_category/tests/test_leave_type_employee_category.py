# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from datetime import timedelta

from lxml import etree

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

    # ─── Types offered by the form ──────────────────────────────────
    def _searched_ids(self, employee=None, **context):
        """Return the ids of the types a search offers for the given employee.

        The very search the time off type field of both forms does, which pass
        ``employee_id`` in its context themselves.

        :returns: list of hr.leave.type ids
        """
        LeaveType = self.env["hr.leave.type"]
        if employee is not None:
            context["employee_id"] = employee.id
        return LeaveType.with_context(**context).search([]).ids

    def test_search_offers_restricted_type_on_matching_tag(self):
        """The search offers a restricted type to an employee holding one of its tags."""
        offered = self._searched_ids(self.tagged_employee)
        self.assertIn(self.restricted_type.id, offered)
        self.assertIn(self.open_type.id, offered)

    def test_search_hides_restricted_type_without_tag(self):
        """The search hides a restricted type from the employees holding none of its tags."""
        offered = self._searched_ids(self.other_employee)
        self.assertNotIn(self.restricted_type.id, offered)
        self.assertIn(self.open_type.id, offered)

        offered = self._searched_ids(self.untagged_employee)
        self.assertNotIn(self.restricted_type.id, offered)
        self.assertIn(self.open_type.id, offered)

    def test_search_offers_restricted_type_on_default_employee_id(self):
        """``default_employee_id`` designates the employee just as well.

        It is the key the form of a time off opened for somebody else carries.
        """
        self.assertNotIn(
            self.restricted_type.id,
            self._searched_ids(default_employee_id=self.other_employee.id),
        )

    def test_search_unfiltered_without_employee_in_context(self):
        """No employee designated, nothing filtered.

        The configuration list must show every type, whoever opens it: an employee
        holding a restricted tag may also hold the Time Off officer rights.
        """
        self.assertIn(self.restricted_type.id, self._searched_ids())

    def test_search_filter_can_be_skipped(self):
        """The filter steps aside for the server-side code that needs every type."""
        self.assertIn(
            self.restricted_type.id,
            self._searched_ids(
                self.other_employee, skip_leave_type_employee_filter=True
            ),
        )

    # ─── Company of the employee ─────────────────────────────────────────────
    def _other_company_setup(self):
        """Return a company of its own, an employee of it and a type of it.

        :returns: tuple (company, employee, leave type)
        """
        company = self.env["res.company"].create({"name": "Foreign Restriction Test Co"})
        employee = self.env["hr.employee"].create(
            {"name": "Foreign Employee Test", "company_id": company.id}
        )
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Foreign Company Leave Test",
                "company_id": company.id,
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )
        return company, employee, leave_type

    def test_search_hides_the_types_of_another_company(self):
        """A type of another company is not offered, both companies being active.

        The native record rule only ever checks the companies of the *user*: an officer
        working with two of them active is otherwise offered the types of both, whichever
        employee the request is for, and nothing refuses the crossing afterwards.
        """
        company, employee, foreign_type = self._other_company_setup()
        offered = (
            self.env["hr.leave.type"]
            .with_context(
                allowed_company_ids=[self.env.company.id, company.id],
                employee_id=self.other_employee.id,
            )
            .search([])
            .ids
        )
        self.assertNotIn(foreign_type.id, offered, "the foreign type is out")
        self.assertIn(self.open_type.id, offered, "the type of their own company is in")

        own = (
            self.env["hr.leave.type"]
            .with_context(
                allowed_company_ids=[self.env.company.id, company.id],
                employee_id=employee.id,
            )
            .search([])
            .ids
        )
        self.assertIn(foreign_type.id, own, "offered for an employee of that company")

    def test_search_keeps_the_types_shared_across_companies(self):
        """A type carrying no company is offered to everybody."""
        shared = self.env["hr.leave.type"].create(
            {
                "name": "Shared Company Leave Test",
                "company_id": False,
                "leave_validation_type": "hr",
                "requires_allocation": "no",
            }
        )
        self.assertIn(shared.id, self._searched_ids(self.other_employee))

    def test_search_leaves_a_domain_stating_its_own_company_alone(self):
        """A caller naming ``company_id`` itself is not second-guessed.

        It knows which company it is after and is not necessarily asking for the
        employee sitting in the context: the batch generation wizards scope their type
        field that way, and a module looking a counter up by company may well target one
        the user is not even allowed. Filling the company of the context employee in
        there would answer nothing at all.
        """
        company, _employee, foreign_type = self._other_company_setup()
        found = (
            self.env["hr.leave.type"]
            .with_context(
                allowed_company_ids=[self.env.company.id, company.id],
                employee_id=self.other_employee.id,
            )
            .search([("company_id", "=", company.id)])
        )
        self.assertIn(foreign_type.id, found.ids)

    def test_search_still_filters_the_tags_on_a_company_domain(self):
        """Stating the company buys nothing on the tags, which stay filtered."""
        found = (
            self.env["hr.leave.type"]
            .with_context(employee_id=self.other_employee.id)
            .search([("company_id", "in", [self.env.company.id, False])])
        )
        self.assertNotIn(self.restricted_type.id, found.ids)

    def test_no_arch_domain_shadows_the_native_type_field(self):
        """No view of ours narrows ``holiday_status_id`` down through its arch.

        Two reasons, both of them regressions the day somebody adds one back:

        * on the allocation the native domain lives on the field in Python
          (``_domain_holiday_status_id``: only the types opened to employee requests
          for a non officer), the arch carrying none, and the web client only falls
          back on the field one when the arch is silent. An arch domain shadows it
          and offers an employee the types HR never opened to their requests.
        * on the time off, the attribute would have to be a copy of the native one,
          to drift on the next migration, and any other module narrowing that same
          attribute down would silently undo ours, or ours theirs.
        """
        for model, view_xmlid, native_domain in (
            ("hr.leave", "hr_holidays.hr_leave_view_form", True),
            (
                "hr.leave.allocation",
                "hr_holidays.hr_leave_allocation_view_form",
                False,
            ),
        ):
            with self.subTest(model=model):
                arch = etree.fromstring(
                    self.env[model].get_view(self.env.ref(view_xmlid).id)["arch"]
                )
                nodes = arch.xpath("//field[@name='holiday_status_id']")
                self.assertTrue(nodes, "the type field is expected on the form")
                domains = {node.get("domain") for node in nodes}
                if native_domain:
                    self.assertNotIn(
                        "restricted_category_ids",
                        " ".join(filter(None, domains)),
                        "the tag restriction has no business in the arch",
                    )
                else:
                    self.assertEqual(
                        domains,
                        {None},
                        "an arch domain here shadows the native one of the field",
                    )
                    self.assertTrue(
                        self.env[model].fields_get(["holiday_status_id"])[
                            "holiday_status_id"
                        ]["domain"],
                        "the native domain of the field is what governs",
                    )

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

    def test_offering_and_default_agree_on_the_same_employee(self):
        """What the form offers and what it defaults on are the one same answer.

        Both go through ``hr.leave.type._search`` keyed on the employee of the context:
        there is no second implementation left to come to disagree with the first, which
        is what a computed list of allowed types next to a default picked another way
        would eventually do. Asserted on both models and both employees.
        """
        for model in ("hr.leave", "hr.leave.allocation"):
            for employee in (self.tagged_employee, self.other_employee):
                with self.subTest(model=model, employee=employee.name):
                    Model = self.env[model].with_context(
                        default_employee_id=employee.id
                    )
                    offered = (
                        self.env["hr.leave.type"]
                        .with_context(employee_id=employee.id)
                        .search([])
                    )
                    default = Model.default_get(
                        ["holiday_status_id", "employee_id"]
                    ).get("holiday_status_id")
                    if default:
                        self.assertIn(
                            default,
                            offered.ids,
                            "the form must never default on a type it does not offer",
                        )
                    for leave_type in offered:
                        self.assertTrue(
                            leave_type._is_allowed_for_employee(employee),
                            "the form must never offer a type the constraint refuses",
                        )

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

    def test_default_type_not_picked_when_employee_in_context(self):
        """The core never picks a type the employee of the context is not entitled to.

        Its own search is filtered like any other, so there is nothing left to drop:
        it defaults on the first type the employee may actually use.
        """
        self._make_restricted_type_the_core_default()
        defaults = (
            self.env["hr.leave"]
            .with_context(default_employee_id=self.other_employee.id)
            .default_get(["holiday_status_id", "employee_id"])
        )
        self.assertNotEqual(
            defaults.get("holiday_status_id"), self.restricted_type.id
        )
        self.assertTrue(
            defaults.get("holiday_status_id"), "a type the employee may use is offered"
        )

    def test_default_type_dropped_when_employee_resolved_by_fallback(self):
        """The core default is cleared when only the fallback resolves the employee.

        The plain *New* of the Time Off list carries no employee in its context: the
        search of the core is therefore not filtered, and it picks a type the employee
        it resolves afterwards may not use. Left alone, the form opens on a type absent
        from the very list it offers next to it.
        """
        self._make_restricted_type_the_core_default()
        user = self.env["res.users"].create(
            {
                "name": "Other Employee User Test",
                "login": "other.employee.user.test",
                "groups_id": [
                    Command.link(self.env.ref("base.group_user").id),
                    Command.link(self.env.ref("hr_holidays.group_hr_holidays_user").id),
                ],
            }
        )
        self.other_employee.user_id = user
        defaults = (
            self.env["hr.leave"]
            .with_user(user)
            .default_get(["holiday_status_id", "employee_id"])
        )
        self.assertEqual(
            defaults.get("employee_id"),
            self.other_employee.id,
            "the fallback is expected to resolve the employee of the user",
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
