# 📧 Guide Complet - Système Email & Notifications Tier 4

## 🎯 Vue d'ensemble

Le système d'email et de notifications est **100% opérationnel** avec:
- ✅ Modèles de base de données (RealtimeNotification, AdvancedDashboard)
- ✅ Admin Django avec actions personnalisées
- ✅ Vues et URLs complètes
- ✅ Configuration email (Console par défaut, SMTP en production)
- ✅ Intégration avec le système existant
- ✅ Templates HTML

---

## 📧 SYSTÈME D'EMAIL

### Configuration

Le système est configuré pour fonctionner en mode **CONSOLE** (affiche les emails dans le terminal).

**Fichier:** `invoice_project/settings.py`

#### Mode Console (Développement) - ACTIF PAR DÉFAUT
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Les emails sont affichés dans la console Django. Parfait pour tester.

#### Mode SMTP (Production) - À CONFIGURER

Pour envoyer de vrais emails, remplacez la configuration par:

**Gmail:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'xxxxx xxxx xxxx xxxx'  # App password!
DEFAULT_FROM_EMAIL = 'noreply@facturation.com'
```

⚠️ **Attention Gmail:** Utilisez un [mot de passe d'application](https://myaccount.google.com/apppasswords), pas votre mot de passe normal.

**Outlook/Hotmail:**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@outlook.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
```

**OVH:**
```python
EMAIL_HOST = 'mail.ovh.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@votre-domaine.fr'
```

---

### Fonctionnalités Email

#### 1. Envoyer une facture par email

**Chemin:** Factures → Cliquer sur facture → Bouton "Envoyer par Email"

**Flux:**
```
Utilisateur clique "Envoyer Email"
    ↓
email_utils.send_invoice_email()
    ↓
EmailMessage créé avec PDF en pièce jointe
    ↓
Email envoyé à: invoice.client.email
    ↓
Notification créée: RealtimeNotification (payment_reminder)
    ↓
AuditLog enregistré
```

**Code:**
```python
from invoice_app.email_utils import send_invoice_email

# Dans une vue:
send_invoice_email(invoice_obj)
```

#### 2. Rappel de paiement

**Chemin:** Factures → Cliquer sur facture → Bouton "Envoyer Rappel"

Envoie un email avant la date d'échéance.

#### 3. Confirmation de paiement

Envoyé automatiquement quand un paiement est enregistré:

**Code:**
```python
from invoice_app.email_utils import send_payment_thank_you

send_payment_thank_you(invoice_obj, payment_amount)
```

#### 4. Types d'emails envoyés

| Type | Déclencheur | Template |
|------|-------------|----------|
| Facture Envoyée | Clic bouton "Envoyer" | invoice_sent.html |
| Rappel Paiement | Clic "Envoyer Rappel" | payment_reminder.html |
| Paiement Reçu | Paiement enregistré | payment_thank_you.html |
| Facture En Retard | Cron/manuel | overdue_invoice.html |
| Devis Envoyé | Clic "Envoyer Devis" | quote_sent.html |
| Devis Accepté | Client accepte | quote_accepted.html |
| Devis Rejeté | Client refuse | quote_rejected.html |
| Alerte Système | Anomalie détectée (Tier 3) | system_alert.html |
| Admin Notification | Event critique | admin_alert.html |

---

## 🔔 SYSTÈME DE NOTIFICATIONS TEMPS RÉEL (Tier 4)

### Accès aux Notifications

**Option 1: Via la cloche 🔔**
- Cloche dans la barre de navigation
- Badge montre le nombre de notifications non-lues
- Cliquez pour voir la liste

**Option 2: Via URL**
- `/notifications/` - Liste complète
- `/dashboard/advanced/` - Widget de notifications

### Types de Notifications (10 types)

```python
NOTIFICATION_TYPES = [
    ('anomaly_critical', 'Anomalie Critique'),
    ('payment_received', 'Paiement Reçu'),
    ('invoice_overdue', 'Facture en Retard'),
    ('alert_acknowledged', 'Alerte Reconnue'),
    ('forecast_updated', 'Prévision Mise à Jour'),
    ('export_completed', 'Export Complété'),
    ('system_alert', 'Alerte Système'),
    ('new_invoice', 'Nouvelle Facture'),
    ('new_quote', 'Nouveau Devis'),
    ('payment_reminder', 'Rappel Paiement'),
]
```

### Niveaux de Priorité

```python
PRIORITY_CHOICES = [
    ('low', 'Basse'),       # 🟢 Information générale
    ('medium', 'Moyenne'),  # 🟡 Important
    ('high', 'Élevée'),     # 🟠 Urgent
    ('critical', 'Critique'),# 🔴 Action requise immédiatement
]
```

### Créer une Notification

**Code:**
```python
from invoice_app.email_utils import create_realtime_notification

notification = create_realtime_notification(
    user=request.user,
    notification_type='payment_received',
    title='Paiement reçu: 500€',
    message='Paiement de 500€ pour facture 2026-001',
    priority='high',
    client=client_obj,
    invoice=invoice_obj,
    action_url='/invoices/1/'
)
```

### Fonctions de Notification

**Dans `email_utils.py`:**

```python
# Nouvelle facture créée
notify_invoice_created(user, invoice)

# Facture envoyée par email
notify_invoice_sent(user, invoice)

# Paiement reçu
notify_payment_received(user, invoice, 500.00)

# Facture en retard
notify_invoice_overdue(user, invoice)

# Nouveau devis créé
notify_quote_created(user, quote)

# Anomalie détectée (Tier 3)
notify_anomaly_detected(user, 'duplicate_invoice', 'Facture dupliquée', 'Facture 2026-001 dupliquée détectée')
```

### API Notifications (AJAX)

#### Marquer comme lue
```
GET /notifications/<id>/mark-read/
```

#### Rejeter/Fermer
```
GET /notifications/<id>/dismiss/
```

#### Compter non-lues
```
GET /api/notifications/unread-count/
Response: {"unread_count": 3, "status": "success"}
```

---

## 📊 TABLEAU DE BORD AVANCÉ (Tier 4)

### Accès

**URLs:**
- `/dashboard/advanced/` - Vue principale
- `/dashboard/settings/` - Paramètres

### Fonctionnalités

**KPIs affichés:**
- Total Clients
- Total Factures
- Chiffre d'Affaires (CA)
- Factures En Attente

**Widgets:**
- Notifications Récentes (5 dernières)
- Alertes Intelligentes (5 dernières, Tier 3)
- Anomalies Détectées (5 dernières, Tier 3)
- Prévisions (dernière, Tier 3)

### Paramètres

**Disponibles dans `/dashboard/settings/`:**

1. **Titre du dashboard** - Personnaliser le nom
2. **Statut** - Activer/désactiver
3. **Période par défaut** - Quotidien, Hebdomadaire, Mensuel, Trimestriel, Annuel
4. **Schéma couleur** - Automatique, Clair, Sombre
5. **Rafraîchissement** - Auto on/off, intervalle (10-300 sec)
6. **Widgets visibles** - Afficher/masquer Prévisions, Anomalies, Alertes

### Base de Données

**Modèle: `AdvancedDashboard`**

```python
user (OneToOneField)           # Un dashboard par utilisateur
title (CharField)              # Titre personnalisé
is_enabled (BooleanField)      # Actif ou pas
widgets_config (TextField)     # Config JSON des widgets
kpi_list (TextField)           # Liste des KPIs JSON
default_period (CharField)     # Période défaut
color_scheme (CharField)       # light/dark/auto
auto_refresh (BooleanField)    # Rafraîchissement auto
refresh_interval (IntegerField)# Secondes (30 par défaut)
show_forecasts (BooleanField)  # Afficher prévisions
show_anomalies (BooleanField)  # Afficher anomalies
show_alerts (BooleanField)     # Afficher alertes
created_at (DateTimeField)     # Date création
updated_at (DateTimeField)     # Date modification
```

---

## 💾 MODÈLES DE DONNÉES

### RealtimeNotification

```python
user (FK User)                 # Qui reçoit
notification_type (CharField)  # Type (10 choices)
title (CharField)              # Titre court
message (TextField)            # Message détaillé
priority (CharField)           # low/medium/high/critical
is_read (BooleanField)         # Lue?
read_at (DateTimeField)        # Quand lue?
is_dismissed (BooleanField)    # Rejetée?
action_url (CharField)         # Lien d'action
created_at (DateTimeField)     # Créé le
expires_at (DateTimeField)     # Expire le (optionnel)
client (FK Client)             # Client lié (optionnel)
invoice (FK Invoice)           # Facture liée (optionnel)

Indexes:
- (user, -created_at)
- (priority, is_read)
- (notification_type)
```

### AdvancedDashboard

Voir section précédente.

---

## 👨‍💼 ADMIN DJANGO

### RealtimeNotificationAdmin

**Accès:** http://localhost:8000/admin/invoice_app/realtimenotification/

**Colonnes affichées:**
- user
- notification_type
- priority
- is_read
- created_at

**Filtres:**
- notification_type
- priority
- is_read
- created_at

**Recherche:**
- title
- message

**Actions:**
- ✓ Marquer comme lue
- ✗ Marquer comme non-lue
- ❌ Rejeter

### AdvancedDashboardAdmin

**Accès:** http://localhost:8000/admin/invoice_app/advanceddashboard/

**Colonnes affichées:**
- user
- is_enabled
- default_period
- color_scheme
- auto_refresh
- updated_at

**Filtres:**
- is_enabled
- default_period
- color_scheme
- auto_refresh

**Actions:**
- ✓ Activer
- ✗ Désactiver
- 🔄 Réinitialiser par défaut

---

## 🧪 TESTER LE SYSTÈME

### 1. Tester via Shell Django

```bash
cd "c:\Users\slima\...\logiciel-de-facturation-main\logiciel-de-facturation-main"
venv\Scripts\python.exe manage.py shell
```

**Créer une notification:**
```python
from django.contrib.auth.models import User
from invoice_app.models import RealtimeNotification

user = User.objects.first()

notif = RealtimeNotification.objects.create(
    user=user,
    notification_type='payment_received',
    title='Test Notification',
    message='Ceci est une notification de test',
    priority='high'
)

print(f"Notification créée: {notif.title}")
```

**Envoyer un email:**
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'Contenu du test',
    'noreply@facturation.com',
    ['votre-email@example.com'],
)
# Check console output
```

### 2. Tester via Admin

1. Allez à http://localhost:8000/admin
2. Invoices App → RealtimeNotification → Add
3. Remplissez le formulaire
4. Save
5. Allez à http://localhost:8000/notifications/ pour voir

### 3. Tester via l'application

1. Créez une facture
2. Allez à sa page de détail
3. Cliquez "Envoyer par Email"
4. Vous verrez:
   - Email dans la console
   - Notification dans le dashboard
   - Notification en haut à droite (cloche)

---

## 🔗 INTÉGRATION AVEC VUES EXISTANTES

### Ajouter une notification à une vue existante

**Fichier:** `invoice_app/views.py`

```python
@login_required
def invoice_create_view(request):
    # ... création facture ...
    
    # Créer une notification
    from invoice_app.email_utils import notify_invoice_created
    notify_invoice_created(request.user, new_invoice)
    
    return redirect('invoice-detail', pk=new_invoice.id)
```

### Dans un modèle (signal)

**Fichier:** `invoice_app/apps.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice, RealtimeNotification
from .email_utils import notify_invoice_created

@receiver(post_save, sender=Invoice)
def invoice_created(sender, instance, created, **kwargs):
    if created:
        # Créer notification pour tous les admins
        from django.contrib.auth.models import User
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            notify_invoice_created(admin, instance)
```

---

## 📝 LOGS & AUDIT

Chaque action est loggée via **AuditLog**:

```python
AuditLog.objects.create(
    action='EMAIL_SENT',
    model='Invoice',
    object_id=invoice.id,
    object_str=f'Facture {invoice.invoice_number}',
    user=request.user.username,
    ip_address=request.META.get('REMOTE_ADDR')
)
```

**Consulter les logs:**
- Admin: http://localhost:8000/admin/invoice_app/auditlog/
- Vue: http://localhost:8000/audit-log/

---

## 🚀 DÉPLOIEMENT EN PRODUCTION

### Checklist

- [ ] Configurer EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD dans settings.py
- [ ] Tester avec un vraie compte email
- [ ] Vérifier les emails arrivent correctement
- [ ] Activer HTTPS/TLS si possible
- [ ] Monitorer les erreurs d'email
- [ ] Configurer les dossiers de log
- [ ] Tester les notifications sur plusieurs utilisateurs

### Variables d'environnement (recommandé)

```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=votre-email@gmail.com
export EMAIL_HOST_PASSWORD=xxxxx xxxx xxxx xxxx
```

Puis dans settings.py:
```python
if os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    # ... etc
```

---

## 📞 SUPPORT

### Erreurs courantes

**1. "SMTPAuthenticationError"**
- ❌ Mauvais mot de passe
- ✅ Solution: Vérifier EMAIL_HOST_USER et EMAIL_HOST_PASSWORD

**2. "SMTPNotSupportedError"**
- ❌ TLS/SSL non supporté
- ✅ Solution: Essayer EMAIL_USE_SSL = True à la place de EMAIL_USE_TLS

**3. Emails non envoyés en production**
- ❌ Firewall bloque le port SMTP
- ✅ Solution: Vérifier les règles firewall, contacter l'hébergeur

**4. Notifications ne s'affichent pas**
- ❌ JavaScript désactivé ou modèle manquant
- ✅ Solution: Vérifier la console navigateur pour erreurs

---

**✅ Système 100% opérationnel et prêt à l'emploi!**
