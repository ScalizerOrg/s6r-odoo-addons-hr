# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer HR Leave Only HR',
    'version': '18.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Restrict some leave types to HR managers only",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'hr_holidays',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module adds an "HR Only" flag on leave types. Leave types flagged as HR Only
are reserved for HR managers: they do not appear in the employee leave request form
and a server-side constraint prevents non-HR users from using them.
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
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
