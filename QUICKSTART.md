# Django Invoice Application - Quick Start Guide

## 🎯 Démarrage Rapide (5 minutes)

### 1️⃣ Configuration de l'Environnement

```powershell
# Windows PowerShell
cd invoice_web
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 2️⃣ Installation des Dépendances

```bash
pip install -r requirements.txt
```

### 3️⃣ Initialisation de la Base de Données

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4️⃣ Créer un Compte Admin

```bash
python manage.py createsuperuser
```

### 5️⃣ Lancer le Serveur

```bash
python manage.py runserver
```

### 6️⃣ Accédez à l'Application

- **Application Web** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin

---

## 📖 Guide d'Utilisation

### Tableau de Bord
- Visualisez les statistiques principales
- Créez une nouvelle facture rapidement
- Consultez les factures récentes

### Gestion des Clients
1. Allez à **Clients** dans le menu
2. Cliquez sur **Ajouter un client**
3. Remplissez les informations
4. Sauvegardez

### Créer une Facture
1. Cliquez sur **Nouvelle facture**
2. Sélectionnez le client
3. Remplissez les dates
4. Cliquez **Créer la facture**
5. Ajoutez les articles
6. Configurez les réductions
7. Exportez en PDF

### Export PDF
- Depuis la fiche facture : **PDF** button
- Le fichier se télécharge automatiquement

### Export Excel
- Depuis la liste des factures : **Exporter Excel** button
- Fichier au format .xlsx

---

## ⚙️ Configuration

### Modifier le Dossier de Configuration
Éditez `invoice_web/invoice_project/settings.py` :

```python
# Langue
LANGUAGE_CODE = 'fr-fr'

# Fuseau horaire
TIME_ZONE = 'Europe/Paris'

# Clé secrète (générer une nouvelle en production)
SECRET_KEY = 'votre-clé-secrète'

# Hôtes autorisés
ALLOWED_HOSTS = ['*']  # À restreindre en production
```

---

## 🗄️ Base de Données

### Tables Principales
- **clients** : Données clients
- **products** : Catalogue produits
- **invoices** : Factures
- **invoice_items** : Lignes de factures
- **payments** : Historique paiements
- **company_info** : Infos entreprise

### Télécharger/Restaurer Données
```bash
# Exporter
python manage.py dumpdata > backup.json

# Importer
python manage.py loaddata backup.json
```

---

## 📊 Fichiers Importants

| Fichier | Description |
|---------|-------------|
| `models.py` | Modèles de données |
| `views.py` | Logique métier |
| `forms.py` | Formulaires |
| `urls.py` | Routes de l'application |
| `settings.py` | Configuration Django |
| `manage.py` | Commandes Django |

---

## 🔧 Commandes Utiles

```bash
# Créer les tables
python manage.py migrate

# Générer les migrations
python manage.py makemigrations

# Ouvrir le shell Python
python manage.py shell

# Collecter les fichiers statiques
python manage.py collectstatic

# Nettoyer la base
python manage.py flush

# Tester l'application
python manage.py test
```

---

## 🐛 Troubleshooting

### ❌ "Port 8000 already in use"
```bash
python manage.py runserver 8001
```

### ❌ "ModuleNotFoundError: No module named 'django'"
```bash
pip install -r requirements.txt
```

### ❌ "Template does not exist"
Vérifiez que les templates se trouvent dans `invoice_app/templates/`

### ❌ Base de données corrompue
```bash
# Réinitialiser complètement
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## 🚀 Améliorations Futures

- [ ] Authentification utilisateurs
- [ ] Multi-utilisateurs
- [ ] Dashboard analytique avancé
- [ ] API REST complète
- [ ] Webhooks
- [ ] Email automatique
- [ ] Factures récurrentes
- [ ] Système de devis
- [ ] Gestion d'inventaire
- [ ] Mobile responsive amélioré

---

## 📚 Documentation Externe

- [Django Docs](https://docs.djangoproject.com/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [ReportLab](https://www.reportlab.com/)

---

**Bon travail! 🎉**
