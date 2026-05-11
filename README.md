# Django Invoice Web Application

Application de facturation moderne avec Django - Conversion du desktop app Python Tkinter en application web.

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8+
- pip

### Étape 1: Créer un environnement virtuel

```bash
cd invoice_web
python -m venv venv

# Activation
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Étape 2: Installer les dépendances

```bash
pip install -r requirements.txt
```

### Étape 3: Initialiser la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

### Étape 4: Créer un superuser (admin)

```bash
python manage.py createsuperuser
```

Entrez :
- Nom d'utilisateur: `admin`
- Email: (appuyez sur Entrée)
- Mot de passe: (entrez un mot de passe)

### Étape 5: Lancer le serveur

```bash
python manage.py runserver
```

Accédez à l'application : `http://localhost:8000`

---

## 📋 Structure du Projet

```
invoice_web/
├── manage.py                 # Utilitaire Django
├── requirements.txt          # Dépendances
├── invoice_project/          # Configuration Django
│   ├── settings.py          # Paramètres
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # WSGI
├── invoice_app/             # Application Django
│   ├── models.py            # Modèles (Client, Invoice, etc.)
│   ├── views.py             # Vues (logique)
│   ├── forms.py             # Formulaires
│   ├── admin.py             # Interface admin
│   ├── urls.py              # URLs de l'app
│   ├── migrations/          # Migrations BD
│   ├── templates/           # Templates HTML
│   │   ├── base.html        # Template de base
│   │   └── invoice_app/     # Templates spécifiques
│   └── static/              # CSS, JS
```

---

## 🎯 Fonctionnalités

### Dashboard
- 📊 Statistiques en temps réel
- 📈 Chiffre d'affaires
- 📋 Factures récentes

### Gestion des Clients
- ✅ Ajouter/Modifier/Supprimer
- 📍 Adresses de livraison et facturation
- 🌍 Support multi-pays
- 🏷️ TVA Intracommunautaire

### Gestion des Produits
- ✅ Catalogue de produits
- 💰 Gestion des prix
- 📦 Références uniques

### Gestion des Factures
- 📝 Création factures automatiques
- 🔢 Numérotation auto (YYYY-NNN)
- 🎁 Remise, Rabais, Escompte
- 💸 Calcul TVA intelligente
- 💳 Suivi des paiements
- 📄 Export PDF
- 📊 Export Excel

### Gestion des Paiements
- 💰 Enregistrement paiements
- 📈 Suivi statuts (En attente, Payée, Partielle)
- 🧾 Historique paiements

### Informations Entreprise
- 🏢 Données entreprise
- 📋 Identifiants fiscaux (SIRET, SIREN, TVA)
- 🎨 Logo

---

## 🔐 Administration

Accédez à l'interface admin : `http://localhost:8000/admin/`

Connectez-vous avec le superuser créé.

---

## 🛠️ Commandes Utiles

```bash
# Créer les tables
python manage.py migrate

# Créer des migrations
python manage.py makemigrations

# Charger des données
python manage.py loaddata data.json

# Shell Django
python manage.py shell

# Vider la base
python manage.py flush

# Créer un superuser supplémentaire
python manage.py createsuperuser
```

---

## 📱 API Endpoints

### Résumé des factures
```
GET /api/invoice/summary/
```
Réponse:
```json
{
  "total_invoices": 42,
  "total_revenue": 12500.50,
  "paid": 35,
  "pending": 7
}
```

### Prix d'un produit
```
GET /api/product/<product_id>/price/
```

---

## 🎨 Personnalisation

### Changer les couleurs
Modifiez `base.html` (variables CSS) :
```css
:root {
    --primary-color: #4a90e2;
    --secondary-color: #f5f7fa;
}
```

### Ajouter des champs
1. Modifiez `models.py`
2. Créez une migration : `python manage.py makemigrations`
3. Appliquez : `python manage.py migrate`

---

## 🚀 Déploiement

### Production (Gunicorn + Nginx)

```bash
# Installer Gunicorn
pip install gunicorn

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Lancer Gunicorn
gunicorn invoice_project.wsgi:application --bind 0.0.0.0:8000
```

### Variables d'environnement (.env)
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://...
```

---

## 📊 Modèles de Données

### Client
- Nom, Email, Téléphone
- Adresses (livraison, facturation)
- Pays, TVA Intracommunautaire

### Product
- Nom, Prix, Référence
- Description

### Invoice
- Numéro, Client, Date
- Articles, Totaux
- Réductions (Remise, Rabais, Escompte)
- TVA, Paiements

### Payment
- Facture, Montant, Méthode
- Date, Référence

---

## 🐛 Dépannage

### Port 8000 déjà utilisé
```bash
python manage.py runserver 8001
```

### Base de données corrompue
```bash
# Supprimer db.sqlite3 et les migrations
rm db.sqlite3
rm invoice_app/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

### Template non trouvé
Vérifiez que TEMPLATES['DIRS'] pointe vers le bon dossier dans `settings.py`

---

## 📞 Support

Pour toute question ou bug, consultez la documentation Django officielle:
https://docs.djangoproject.com/

---

## 📄 License

MIT License

---

**Créé avec ❤️ pour la gestion de facturation**
