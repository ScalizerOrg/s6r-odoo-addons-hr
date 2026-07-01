Scalizer HR Leave Only HR
===============

This module adds an "HR Only" flag on leave types. Leave types flagged as HR Only
are reserved for HR managers.

## Features

* An **HR Only** checkbox on the leave type configuration form.
* HR-only leave types are hidden from the leave request form for non-HR users.
* A server-side constraint prevents non-HR users from using an HR-only leave
  type, even through direct API calls or URL manipulation.

## Usage

1. Open a leave type (Time Off > Configuration > Leave Types).
2. Enable the **HR Only** option.
3. Only users in the *Time Off / Administrator* group will be able to select
   this leave type when creating a time off request.

## Authors

* Scalizer

## Maintainers

This module is maintained by [Scalizer](https://www.scalizer.fr).

![Scalizer](./static/description/logo.png)
