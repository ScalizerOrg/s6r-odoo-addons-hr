# Copyright 2026 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    'name': 'Scalizer HR Employee Tags Menu',
    'version': '18.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Give HR users access to the employee tags list",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'hr',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
The native Employees > Configuration > Tags menu is reserved to the developer
group, so employee tags can only be maintained from an employee form. This module
opens that menu up to the HR users, which is what a database actually driving
something with those tags (eligibility, restrictions, reporting) needs.
    ''',
    'qweb': [
    ],
    'demo': [
    ],
    'images': [
    ],
    'data': [
        'views/hr_employee_category.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
