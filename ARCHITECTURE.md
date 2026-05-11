PROJET DJANGO CONVERTIE
=======================

📦 invoice_web/
│
├── 📄 manage.py                      # Point d'entrée Django
├── 📄 requirements.txt               # Dépendances Python
├── 📄 .gitignore                     # Git ignore rules
├── 📄 .env.example                   # Variables d'environnement
├── 📄 Dockerfile                     # Docker image
├── 📄 docker-compose.yml             # Docker compose
├── 📄 populate_db.py                 # Script de remplissage BD
├── 📄 README.md                      # Documentation complète
├── 📄 QUICKSTART.md                  # Guide de démarrage rapide
├── 📄 CHANGELOG.md                   # Historique des versions
│
├── 📁 invoice_project/               # Configuration Django
│   ├── 📄 __init__.py
│   ├── 📄 settings.py                # Paramètres Django
│   ├── 📄 urls.py                    # URLs principales
│   └── 📄 wsgi.py                    # Application WSGI
│
├── 📁 invoice_app/                   # Application principale
│   ├── 📄 __init__.py
│   ├── 📄 apps.py                    # Config application
│   ├── 📄 models.py                  # Modèles (Client, Invoice, etc.)
│   ├── 📄 views.py                   # Vues et logique métier
│   ├── 📄 forms.py                   # Formulaires Django
│   ├── 📄 urls.py                    # URLs application
│   ├── 📄 admin.py                   # Interface admin
│   ├── 📄 serializers.py             # Sérialiseurs DRF (API)
│   ├── 📄 tests.py                   # Tests unitaires
│   │
│   ├── 📁 migrations/                # Migrations BD
│   │   └── 📄 __init__.py
│   │
│   ├── 📁 templates/                 # Templates HTML
│   │   ├── 📄 base.html              # Template de base
│   │   └── 📁 invoice_app/
│   │       ├── 📄 dashboard.html
│   │       ├── 📄 invoice_list.html
│   │       ├── 📄 invoice_detail.html
│   │       ├── 📄 invoice_form.html
│   │       ├── 📄 invoice_edit.html
│   │       ├── 📄 invoice_confirm_delete.html
│   │       ├── 📄 client_list.html
│   │       ├── 📄 client_detail.html
│   │       ├── 📄 client_form.html
│   │       ├── 📄 client_confirm_delete.html
│   │       ├── 📄 product_list.html
│   │       ├── 📄 product_detail.html
│   │       ├── 📄 product_form.html
│   │       ├── 📄 product_confirm_delete.html
│   │       ├── 📄 company_info.html
│   │       └── 📄 payment_form.html
│   │
│   └── 📁 static/                    # Fichiers statiques
│       ├── 📁 css/
│       │   └── 📄 style.css          # Styles personnalisés
│       └── 📁 js/
│           └── 📄 main.js            # Scripts

=====================================
MODÈLES DE DONNÉES
=====================================

Client
├── id (PK)
├── name (255 chars)
├── email (email)
├── phone (20 chars)
├── delivery_address (text)
├── billing_address (text)
├── country (100 chars)
├── tva_intra (50 chars)
└── timestamps (created_at, updated_at)

Product
├── id (PK)
├── name (255 chars)
├── price (decimal 10,2)
├── reference (100 chars, unique)
├── description (text)
└── timestamps (created_at, updated_at)

Invoice
├── id (PK)
├── invoice_number (20 chars, unique)
├── client_id (FK)
├── date (date)
├── due_date (date)
├── payment_method (choice)
├── subtotal (decimal)
├── remise_% / remise_€
├── rabais_% / rabais_€
├── escompte_% / escompte_€
├── total_discount (decimal)
├── tva_amount (decimal)
├── total (decimal)
├── amount_paid (decimal)
├── payment_status (choice)
├── is_credit_note (bool)
├── credit_note_reason (text)
└── timestamps

InvoiceItem
├── id (PK)
├── invoice_id (FK)
├── description (255 chars)
├── quantity (int)
├── price (decimal)
├── product_id (FK, nullable)

Payment
├── id (PK)
├── invoice_id (FK)
├── amount (decimal)
├── payment_method (varchar)
├── payment_date (date)
├── reference (100 chars)
├── notes (text)
└── created_at

CompanyInfo
├── id (PK)
├── name (255 chars)
├── address (text)
├── phone (20 chars)
├── email (email)
├── website (url)
├── siret (14 chars)
├── siren (9 chars)
├── tva_number (50 chars)
├── logo (image)
└── country (100 chars)

=====================================
URLs ET ROUTES
=====================================

Tableau de bord:
  GET  /                              (dashboard)

Clients:
  GET  /clients/                      (liste)
  POST /clients/create/               (créer)
  GET  /clients/<id>/                 (détail)
  POST /clients/<id>/update/          (modifier)
  GET  /clients/<id>/delete/          (supprimer)

Produits:
  GET  /products/                     (liste)
  POST /products/create/              (créer)
  GET  /products/<id>/                (détail)
  POST /products/<id>/update/         (modifier)
  GET  /products/<id>/delete/         (supprimer)

Factures:
  GET  /invoices/                     (liste)
  POST /invoices/create/              (créer)
  GET  /invoices/<id>/                (détail)
  POST /invoices/<id>/update/         (modifier)
  GET  /invoices/<id>/delete/         (supprimer)
  GET  /invoices/<id>/export/pdf/     (PDF)
  GET  /invoices/export/excel/        (Excel)

Paiements:
  POST /invoices/<id>/payment/add/    (ajouter)

Paramètres:
  GET  /settings/company-info/        (infos entreprise)

API:
  GET  /api/product/<id>/price/       (prix produit)
  GET  /api/invoice/summary/          (résumé factures)

Admin:
  GET  /admin/                        (interface Django)

=====================================
INSTALLATION RAPIDE
=====================================

1. Environnement virtuel:
   python -m venv venv
   .\venv\Scripts\Activate.ps1  (Windows)
   source venv/bin/activate     (Mac/Linux)

2. Dépendances:
   pip install -r requirements.txt

3. Base de données:
   python manage.py makemigrations
   python manage.py migrate

4. Admin:
   python manage.py createsuperuser

5. Données test (optionnel):
   python populate_db.py

6. Serveur:
   python manage.py runserver

7. Accès:
   App: http://localhost:8000
   Admin: http://localhost:8000/admin/

=====================================
TECHNOLOGIES
=====================================

Backend:
  • Django 4.2.0
  • Django REST Framework 3.14.0
  • PostgreSQL / SQLite
  • ReportLab (PDF)
  • OpenPyXL (Excel)

Frontend:
  • Bootstrap 5.3
  • HTML5
  • CSS3
  • JavaScript ES6

Déploiement:
  • Docker
  • Docker Compose
  • Gunicorn
  • Nginx

=====================================
FEATURES PRINCIPALES
=====================================

✅ Gestion complète des clients
✅ Catalogue produits
✅ Génération factures auto-numérotées
✅ Réductions (Remise, Rabais, Escompte)
✅ Calcul TVA multi-pays
✅ Export PDF professionnels
✅ Export Excel
✅ Suivi paiements
✅ Historique transactions
✅ Interface admin Django
✅ API REST
✅ Support Docker
✅ Design responsive
✅ Multi-langue (FR)
✅ Tests unitaires

=====================================
CONVENTIONS CODE
=====================================

Models:
  • Noms au singulier
  • Timestamps sur toutes les tables
  • ForeignKey avec related_name
  • Verbose names en français

Views:
  • Noms cohérents (ClientListView, etc.)
  • Redirection après POST
  • Messages utilisateur
  • Pagination

Templates:
  • Structure en bloc
  • Bootstrap classes
  • Form rendering
  • Messages flash

URLs:
  • Noms url explicites
  • Namespacing app
  • Pattern cohérent

=====================================

Version: 1.0.0
Date: 2025-05-07
Status: ✅ Production-ready
