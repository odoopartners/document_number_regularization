import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    regularized_document_number = fields.Char(
        string="Stored Document Number",
        copy=False,
        index=True,
        help=(
            "Supplier fiscal number used as Document Number without changing "
            "the internal accounting sequence."
        ),
    )
    previous_document_number = fields.Char(
        string="Original Document Number",
        copy=False,
        readonly=True,
        help=(
            "Document number the vendor bill had before the first update. "
            "This value does not change after later updates."
        ),
    )
    document_number_regularization_date = fields.Datetime(
        string="First Update Date",
        copy=False,
        readonly=True,
        help=(
            "Date and time when the document number was updated for the first "
            "time. Later updates are recorded in the chatter."
        ),
    )
    document_number_regularized_by_id = fields.Many2one(
        comodel_name="res.users",
        string="First Updated by",
        copy=False,
        readonly=True,
        help=(
            "User who performed the first document number update. Later "
            "updates and their users are recorded in the chatter."
        ),
    )

    @api.depends("name", "regularized_document_number")
    def _compute_l10n_latam_document_number(self):
        """Show the regularized fiscal number without changing ``name``."""
        super()._compute_l10n_latam_document_number()
        for move in self.filtered(
            lambda record: record.move_type in ("in_invoice", "in_refund")
            and record.regularized_document_number
        ):
            move.l10n_latam_document_number = move.regularized_document_number

    def _inverse_l10n_latam_document_number(self):
        """Keep the internal accounting sequence on regularized documents."""
        regularized_moves = self.filtered(
            lambda record: record.move_type in ("in_invoice", "in_refund")
            and record.regularized_document_number
        )
        for move in regularized_moves:
            move.regularized_document_number = move.l10n_latam_document_number

        standard_moves = self - regularized_moves
        if standard_moves:
            super(AccountMove, standard_moves)._inverse_l10n_latam_document_number()

    @api.model
    def _normalize_supplier_reference(self, move):
        reference = re.sub(r"\s+", "", (move.ref or "").upper())
        if not re.fullmatch(r"[A-Z0-9]{4}-[0-9]+", reference):
            return False
        return reference

    @api.model
    def _records_label(self, records, limit=15):
        labels = records[:limit].mapped("display_name")
        if len(records) > limit:
            labels.append(_("and %s more documents", len(records) - limit))
        return "\n- " + "\n- ".join(labels)

    def action_regularize_document_number_from_reference(self):
        """Copy valid supplier references to the displayed document number."""
        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(
                _("Only an Accounting Manager can execute this action.")
            )

        moves = self.exists()
        if not moves:
            return False

        wrong_move_type = moves.filtered(
            lambda move: move.move_type not in ("in_invoice", "in_refund")
        )
        if wrong_move_type:
            raise UserError(
                _(
                    "This action can only be used with vendor bills and vendor "
                    "credit notes:%s",
                    self._records_label(wrong_move_type),
                )
            )

        empty_reference = moves.filtered(lambda move: not (move.ref or "").strip())
        if empty_reference:
            raise UserError(
                _(
                    "No document was updated. The Bill Reference is empty in:%s",
                    self._records_label(empty_reference),
                )
            )

        normalized_numbers = {
            move.id: self._normalize_supplier_reference(move) for move in moves
        }
        invalid_reference = moves.filtered(
            lambda move: not normalized_numbers[move.id]
        )
        if invalid_reference:
            raise UserError(
                _(
                    "No document was updated. The Bill Reference must use the "
                    "XXXX-XXXX format (four alphanumeric characters, a hyphen "
                    "and a numeric sequence). Review:%s",
                    self._records_label(invalid_reference),
                )
            )

        regularization_date = fields.Datetime.now()
        regularized_by = self.env.user.id
        updated = 0
        unchanged = 0

        for move in moves:
            new_number = normalized_numbers[move.id]
            current_number = (
                move.regularized_document_number
                or move.l10n_latam_document_number
                or move.name
            )
            if move.regularized_document_number == new_number:
                move.message_post(
                    body=_(
                        "Document Number unchanged: %(number)s",
                        number=new_number,
                    ),
                    subtype_xmlid="mail.mt_note",
                )
                unchanged += 1
                continue

            values = {
                "regularized_document_number": new_number,
            }
            if not move.previous_document_number:
                values.update(
                    {
                        "previous_document_number": current_number,
                        "document_number_regularization_date": regularization_date,
                        "document_number_regularized_by_id": regularized_by,
                    }
                )
            move.write(values)
            move.message_post(
                body=_(
                    "Document Number updated: %(old_number)s → %(new_number)s",
                    old_number=current_number,
                    new_number=new_number,
                ),
                subtype_xmlid="mail.mt_note",
            )
            updated += 1

        message = _("%s documents were updated.", updated)
        if unchanged:
            message += " " + _(
                "%s already had the same document number.", unchanged
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Document number update completed"),
                "message": message,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
