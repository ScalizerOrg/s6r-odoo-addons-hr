# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    'name': 'Scalizer HR Leave Type Employee Tags',
    'version': '18.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Restrict time off types to employees holding given tags",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'hr_holidays',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module adds a "Restricted to Tags" field on time off types. A type carrying
tags is only available to the employees holding at least one of them:

* the time off and the allocation forms only offer the types the employee is
  entitled to;
* a server-side constraint refuses any other crossing, whatever creates it
  (import, custom wizard, another module), so the restriction cannot be bypassed.

The employee tags list itself is only reachable from an employee form: install
s6r_hr_employee_category_menu to get it as a menu of its own.

A type carrying no tag stays available to everybody. The constraint only applies
on write: time off and allocations already recorded for an employee who later
loses a tag are left untouched.
    ''',
    'qweb': [
    ],
    'demo': [
    ],
    'images': [
    ],
    'data': [
        'views/hr_leave_type.xml',
        'views/hr_leave.xml',
        'views/hr_leave_allocation.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
