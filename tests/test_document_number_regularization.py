from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDocumentNumberRegularization(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Supplier"})

    def _create_move(self, reference):
        return self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "journal_id": self.purchase_journal.id,
                "partner_id": self.partner.id,
                "ref": reference,
                "name": "BILL/2026/08/0006",
            }
        )

    def test_regularize_number_without_changing_internal_number(self):
        move = self._create_move("FC77-25215")
        internal_number = move.name
        previous_document_number = move.l10n_latam_document_number

        move.action_regularize_document_number_from_reference()

        self.assertEqual(move.name, internal_number)
        self.assertEqual(move.l10n_latam_document_number, "FC77-25215")
        self.assertEqual(move.previous_document_number, previous_document_number)
        self.assertEqual(move.document_number_regularized_by_id, self.env.user)
        self.assertTrue(move.document_number_regularization_date)

    def test_short_correlative_is_preserved_without_zero_padding(self):
        move = self._create_move("E001-6")

        move.action_regularize_document_number_from_reference()

        self.assertEqual(move.regularized_document_number, "E001-6")
        self.assertEqual(move.l10n_latam_document_number, "E001-6")
        self.assertEqual(move.name, "BILL/2026/08/0006")

    def test_each_change_is_logged_and_first_audit_data_is_preserved(self):
        move = self._create_move("F001-0001")

        move.action_regularize_document_number_from_reference()
        first_date = move.document_number_regularization_date
        first_user = move.document_number_regularized_by_id
        original_number = move.previous_document_number

        move.ref = "F001-0011"
        move.action_regularize_document_number_from_reference()

        self.assertEqual(move.regularized_document_number, "F001-0011")
        self.assertEqual(move.document_number_regularization_date, first_date)
        self.assertEqual(move.document_number_regularized_by_id, first_user)
        self.assertEqual(move.previous_document_number, original_number)
        self.assertTrue(
            move.message_ids.filtered(
                lambda message: "Document Number updated: F001-0001 → F001-0011"
                in message.body
            )
        )

    def test_unchanged_execution_is_logged(self):
        move = self._create_move("F001-0001")
        move.action_regularize_document_number_from_reference()

        move.action_regularize_document_number_from_reference()

        self.assertTrue(
            move.message_ids.filtered(
                lambda message: "Document Number unchanged: F001-0001"
                in message.body
            )
        )

    def test_empty_reference_aborts_the_whole_batch(self):
        valid_move = self._create_move("F001-125")
        invalid_move = self._create_move(False)

        with self.assertRaises(UserError):
            (valid_move | invalid_move).action_regularize_document_number_from_reference()

        self.assertFalse(valid_move.regularized_document_number)

    def test_invalid_reference_aborts_the_whole_batch(self):
        move = self._create_move("BILL/2026/08/0006")

        with self.assertRaises(UserError):
            move.action_regularize_document_number_from_reference()

        self.assertFalse(move.regularized_document_number)
