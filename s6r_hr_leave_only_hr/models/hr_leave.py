# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

HR_GROUP = "hr_holidays.group_hr_holidays_manager"


class HrLeave(models.Model):
    """Extension of hr.leave to restrict HR-only leave types to HR managers."""

    _inherit = "hr.leave"

    hr_only_visible = fields.Boolean(
        compute="_compute_hr_only_visible",
    )

    def _is_hr_user(self):
        """Return True if the current user belongs to the HR holidays user group.

        :returns: bool
        """
        return self.env.user.has_group(HR_GROUP)

    @api.depends_context("uid")
    def _compute_hr_only_visible(self):
        """Compute whether HR-only leave types should be visible to the current user.

        :returns: None
        """
        is_hr = self._is_hr_user()
        for leave in self:
            leave.hr_only_visible = is_hr

    @api.model
    def default_get(self, fields_list):
        """Set hr_only_visible and clear any pre-selected HR-only leave type for non-HR users.

        hr_only_visible must be in defaults so the domain is evaluated correctly
        on new records (newID) before the computed field is fetched from the server.

        :param fields_list: list of field names requested
        :returns: dict of default values
        """
        defaults = super().default_get(fields_list)
        is_hr = self.env.user.has_group(HR_GROUP)
        if "hr_only_visible" in fields_list:
            defaults["hr_only_visible"] = is_hr
        if not is_hr:
            leave_type_id = defaults.get("holiday_status_id")
            if leave_type_id:
                leave_type = self.env["hr.leave.type"].browse(leave_type_id)
                if leave_type.hr_only:
                    defaults["holiday_status_id"] = False
        return defaults

    @api.constrains("holiday_status_id")
    def _check_hr_only_type(self):
        """Enforce that only HR users can use HR-only leave types.

        This server-side constraint prevents bypassing the view domain restriction
        via direct API calls or URL manipulation.

        :raises ValidationError: When a non-HR user selects an HR-only leave type.
        :returns: None
        """
        if self.env.user.has_group(HR_GROUP):
            return
        for leave in self:
            if leave.holiday_status_id.hr_only:
                raise ValidationError(
                    _(
                        "This leave type can only be used by HR managers. "
                        "Please contact your HR department."
                    )
                )
