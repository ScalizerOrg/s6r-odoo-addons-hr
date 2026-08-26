Scalizer HR Leave Type Employee Tags
===============

This module restricts time off types to the employees holding given employee tags.

## Features

* A **Restricted to Tags** field on the time off type configuration form, next to
  the responsible persons. Empty means no restriction.
* The time off and the allocation forms only offer the types the tags of the
  employee entitle them to.
* A server-side constraint on `hr.leave` and `hr.leave.allocation` refuses any
  other crossing, whatever creates it: import, custom wizard, another module.
  This constraint, not the form domain, is the actual lock.

The employee tags list itself stays where Odoo puts it, reachable from an employee
form only. Install `s6r_hr_employee_category_menu` to get the
*Employees > Configuration > Tags* menu opened up to the HR users.

## Usage

1. Open a time off type (Time Off > Configuration > Time Off Types).
2. Fill in **Restricted to Tags** with the employee tags allowed to use it.
3. Only the employees holding at least one of these tags may request that type,
   or be credited an allocation on it.

## Known limitations

* The constraint only applies on write. An employee losing a tag keeps the time
  off and the allocations already recorded on a type they no longer qualify for:
  the history is not challenged retroactively.
* The form domain replaces the `domain` attribute of the time off type field as a
  whole. Another module doing the same on the same view overrides it — the
  server-side constraint still holds.

## Authors

* Scalizer

## Maintainers

This module is maintained by [Scalizer](https://www.scalizer.fr).

![Scalizer](./static/description/logo.png)
