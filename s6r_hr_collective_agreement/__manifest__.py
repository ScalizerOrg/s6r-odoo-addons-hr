# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer HR CBA Coefficient',
    'version': '18.0.0.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Collective Bargaining Agreement Coefficient",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'hr_contract',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module adds a CBA (Collective Bargaining Agreement) model to manage the position and coefficient of the employees.
    ''',
    'qweb': [
    ],
    'demo': [
    ],
    'images': [
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_cba_position_views.xml',
        'views/hr_contract_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
