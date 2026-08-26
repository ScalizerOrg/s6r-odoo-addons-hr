Scalizer HR Employee Tags Menu
===============

This module gives the HR users access to the employee tags list.

## Features

* The native **Employees > Configuration > Tags** menu, reserved to the developer
  group (`base.group_no_one`), is opened up to the *Employees / Officer* group
  (`hr.group_hr_user`).

## Known limitations

* The module writes on the native menu rather than adding one of its own, so that
  a database in developer mode does not end up with two Tags entries. An uninstall
  does not restore the original group.

## Authors

* Scalizer

## Maintainers

This module is maintained by [Scalizer](https://www.scalizer.fr).

![Scalizer](./static/description/logo.png)
