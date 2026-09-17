{
    "name": "Document Number Update",
    "version": "19.0.1.0.11",
    "author": "Ganemo",
    "maintainer": "Ganemo",
    "website": "https://www.ganemo.co",
    "module_type": "official",
    "category": "Accounting",
    "summary": (
        "Update vendor document numbers from bill references without "
        "changing internal accounting numbers"
    ),
    "description": """
Update vendor bill and credit note document numbers from their supplier
references while preserving Odoo's internal accounting number and a complete
audit trail.
    """,
    "live_test_url": "https://www.ganemo.co/demo",
    "license": "OPL-1",
    "icon": "/account_document_number_regularization/static/description/icon.svg",
    "depends": [
        "account",
        "l10n_latam_invoice_document",
    ],
    "data": [
        "views/account_move_views.xml",
        "views/account_move_actions.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
