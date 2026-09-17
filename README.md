# Document Number Update

**Author:** [Ganemo](https://www.ganemo.co)

**Lead contributor:** [Jonathan Yncio Salazar](https://www.linkedin.com/in/jonathanynciosalazar/)

Functional analysis and development coordination.

## Overview

This Odoo 19 module lets Accounting Managers update vendor document
numbers in bulk using the value entered in **Bill Reference**, without changing
Odoo's internal accounting sequence.

## Key features

The action is available from vendor bills and vendor credit notes. It:

- validates the `XXXX-XXXX` supplier reference format;
- preserves the internal accounting sequence (`BILL/2026/...`);
- exposes the regularized value through Odoo's **Document Number** field;
- stores the original document number, first update date and user;
- logs every document number update in the chatter;
- aborts the complete selection when one record is invalid.

The module is independent from any country-specific localization. Localization
and statutory reporting modules continue to use Odoo's standard **Document
Number** field.

## Usage

1. Open the vendor bills list.
2. Select the bills or vendor credit notes to update.
3. Choose **Actions > Update Document Number from Bill Reference**.

Only users in the Accounting Manager group can run the action.

## Validation rules

- Bill Reference is required.
- The accepted format is `XXXX-XXXX`: four alphanumeric characters, a hyphen
  and a numeric sequence.
- The action only accepts vendor bills and vendor credit notes.
- If one selected document is invalid, none of the selected documents is
  updated.

## Audit information

The **Other Info** tab permanently stores the first update information:

- original document number;
- first update date;
- user who executed the first update.

Every subsequent change is logged in the chatter with the user, date, previous
value and new value.

## Compatibility

- Odoo 19 Community and Enterprise.
- Odoo.sh, Ganemo Online and Ganemo.SH.

---

Developed and maintained by [Ganemo](https://www.ganemo.co), with functional
analysis and development coordination by
[Jonathan Yncio Salazar](https://www.linkedin.com/in/jonathanynciosalazar/).
