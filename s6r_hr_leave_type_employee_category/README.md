Scalizer HR Leave Type Employee Tags
===============

This module restricts time off types to the employees holding given employee tags.

## Features

* A **Restricted to Tags** field on the time off type configuration form, next to
  the responsible persons. Empty means no restriction.
* The time off and the allocation forms only offer the types the tags of the
  employee entitle them to, **and only those of the company of that employee**
  (plus the types shared across companies). The native record rule only ever checks
  the companies of the *user*, so an officer working with two companies active is
  otherwise offered the types of both, whichever employee the request is for — and
  nothing refuses the crossing afterwards.
* The filtering is done on the `hr.leave.type` search, against the employee those
  forms already pass in the context of the type field: no `domain` attribute of the
  native views is replaced, so the native restrictions and those of any other module
  narrowing that same field down keep applying.
* A server-side constraint on `hr.leave` and `hr.leave.allocation` refuses any
  other crossing, whatever creates it: import, custom wizard, another module.
  This constraint, not the filtering of the form, is the actual lock.
* The two batch generation wizards, *Generate Time Off* and *Generate Allocation*,
  pick the type first and the employees second, so it is the employees they sort
  out. Named employees the type is not open to stop the generation, which names
  every one of them; a whole company, department or tag only generates for the
  part of that population the type concerns.

The employee tags list itself stays where Odoo puts it, reachable from an employee
form only. Install `s6r_hr_employee_category_menu` to get the
*Employees > Configuration > Tags* menu opened up to the HR users.

## Usage

1. Open a time off type (Time Off > Configuration > Time Off Types).
2. Fill in **Restricted to Tags** with the employee tags allowed to use it.
3. Only the employees holding at least one of these tags may request that type,
   or be credited an allocation on it.

### Batch generation

The two wizards treat a list of employees and a population differently on purpose:

| Allocation mode | Employees the type is not open to |
| --- | --- |
| By Employee | the generation is refused, naming all of them |
| By Company / Department / Employee Tag | dropped, the others are generated |

The reasoning: a list was typed in one by one, so dropping one silently would hide
a mistake, whereas a population is by definition only partly concerned by a
restricted type. A population leaving nobody at all is refused too, a generation
over an empty set being a silent no-op otherwise.

## Known limitations

* The constraint only applies on write. An employee losing a tag keeps the time
  off and the allocations already recorded on a type they no longer qualify for:
  the history is not challenged retroactively.
* The search is only filtered when the context designates an employee, which is
  what tells a screen where somebody books from a screen where somebody
  administers. The time off type configuration list is therefore never filtered:
  an officer holding a restricted tag themselves still sees every type there.
* Server-side code needing every type whatever the context may pass
  `skip_leave_type_employee_filter` in it.
* The company of the employee is only filled in for a search that says nothing about
  `company_id`. A caller naming it knows which company it wants and is not
  necessarily asking for the employee sitting in the context: the batch generation
  wizards scope their type field on their own company field, and a module looking a
  type up by company may well target one the user is not even allowed.
* Only the tag restriction is backed by a constraint. The company alignment is a
  filtering of what the forms offer, not a lock: an import or a custom wizard
  crossing an employee with a type of another company is not refused, as the native
  does not refuse it either.
* The Time Off dashboard counters are not filtered: the core resolves the employee
  after searching the types. It only ever shows the types the employee holds an
  allocation on, which the constraint would have refused to create, so what may
  show there is the counter of a tag lost afterwards — consistent with the
  retroactivity rule above.

## Authors

* Scalizer

## Maintainers

This module is maintained by [Scalizer](https://www.scalizer.fr).

![Scalizer](./static/description/logo.png)
