# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Whatsapp Broker",
    "summary": """
        Set a broker for whatsapp""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Creu Blanca, Dixmit, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/social",
    "depends": ["mail_broker", "phone_validation"],
    "external_dependencies": {"python": ["requests_toolbelt"]},
    "data": [
        "wizards/whatsapp_composer.xml",
        "views/mail_broker.xml",
        # "templates/assets.xml",
    ],
    "assets": {
        "mail.assets_messaging": [
            "mail_broker_whatsapp/static/src/models/**/*.js",
            "mail_broker_whatsapp/static/src/components/**/*.xml",
        ],
    },
    "qweb": ["static/src/xml/thread.xml"],
}
