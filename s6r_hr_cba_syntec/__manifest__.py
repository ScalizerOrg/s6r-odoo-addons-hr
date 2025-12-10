# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer HR Syntec CBA',
    'version': '18.0.0.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Syntec Collective Bargaining Agreement",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        's6r_hr_collective_agreement',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module adds Syntec CBA data.
    ''',
    'qweb': [
    ],
    'demo': [
    ],
    'images': [
    ],
    'data': [
        'data/hr_cba_data.xml',
        'data/hr_cba_position_data.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
