# 📋 SCÉNARIO DE TEST COMPLET - Application Facturation

**Server**: http://127.0.0.1:8000/  
**Date**: 12 mai 2026

---

## 🎯 PLAN DE TEST GLOBAL

Ce document couvre tous les tests pour valider:
- ✅ Tier 1: Devis, Email, Statistiques, Audit
- ✅ Tier 2: Multi-devise, Recherche, Archivage

---

## 📊 PARTIE 1: SETUP & DONNÉES INITIALES

### Étape 1.1 - Accéder au Dashboard
**URL**: http://127.0.0.1:8000/  
**Attendu**: Page d'accueil avec 6 sections principales
- 📄 Factures
- 📋 Devis
- 👥 Clients
- 📦 Produits
- 💼 Informations Entreprise
- ⚙️ Paramètres

**Vérifier**:
- ✓ Navigation fonctionnelle
- ✓ Liens de menu actifs
- ✓ Pas de 404 ou erreurs

---

### Étape 1.2 - Créer une Entreprise
**URL**: http://127.0.0.1:8000/settings/company-info/  
**Action**: Remplir les infos:
```
Nom: Acme Solutions SARL
Siret: 12345678901234
SIREN: 123456789
TVA Intracommunautaire: FR12345678901
Adresse: 123 Rue de la Paix, 75000 Paris
Téléphone: +33 1 23 45 67 89
Email: info@acme.fr
Site: www.acme.fr
Pays: France
```

**Vérifier**:
- ✓ Formulaire sauvegardé
- ✓ Données affichées dans les PDF/factures

---

### Étape 1.3 - Créer 3 Clients
**URL**: http://127.0.0.1:8000/clients/create/

**Client 1 - France (EUR)**:
```
Nom: Technopark Inc
Email: contact@technopark.fr
Téléphone: +33 6 12 34 56 78
Adresse Livraison: 456 Avenue Tech, 75001 Paris
Adresse Facturation: 456 Avenue Tech, 75001 Paris
Pays: France
TVA: FR98765432101
```

**Client 2 - USA (USD)**:
```
Nom: Silicon Valley Corp
Email: orders@silicon.us
Téléphone: +1 408 123 4567
Adresse Livraison: 1000 Tech Drive, San Jose, CA 95110, USA
Adresse Facturation: Same
Pays: USA
TVA: 98-7654321
```

**Client 3 - UK (GBP)**:
```
Nom: London Financial Ltd
Email: accounts@london.co.uk
Téléphone: +44 20 1234 5678
Adresse Livraison: 100 Finance Street, London, UK
Adresse Facturation: Same
Pays: UK
TVA: GB987654321
```

**Vérifier**:
- ✓ Les 3 clients créés
- ✓ Emails présents
- ✓ Adresses complètes

---

### Étape 1.4 - Créer 5 Produits
**URL**: http://127.0.0.1:8000/products/create/

```
Produit 1 - Consultation:
  Nom: Consultation Expert (100h)
  Référence: CONS-001
  Prix: 150.00 EUR
  Description: Heures de consultation expert

Produit 2 - Développement:
  Nom: Développement Django
  Référence: DEV-001
  Prix: 85.00 EUR
  Description: Services de développement web Django

Produit 3 - Maintenance:
  Nom: Maintenance Annuelle
  Référence: MAIN-001
  Prix: 2500.00 EUR
  Description: Contrat de maintenance annuelle

Produit 4 - Formation:
  Nom: Formation Python
  Référence: FORM-001
  Prix: 1200.00 EUR
  Description: Session de formation Python

Produit 5 - Support:
  Nom: Support Premium 24/7
  Référence: SUP-001
  Prix: 5000.00 EUR
  Description: Support premium avec réponse 24h
```

**Vérifier**:
- ✓ 5 produits créés
- ✓ Prix décimaux corrects
- ✓ Références uniques

---

## 🎯 PARTIE 2: TIER 1 - DEVIS & FACTURES

### Étape 2.1 - Créer un Devis
**URL**: http://127.0.0.1:8000/quotes/create/

**Devis 1**:
```
Client: Technopark Inc
Date: 12/05/2026
Date Validité: 26/05/2026
Articles:
  - Consultation (2) @ 150 = 300 EUR
  - Formation (1) @ 1200 = 1200 EUR
Remise: 10% = 150 EUR
TVA: 20%
Terms: Conditions standard, Paiement 30 jours
```

**Attendu**:
- Numéro auto: DEV-2026-001
- Total: (300 + 1200 - 150) * 1.20 = 1,848.00 EUR
- ✓ Statut: Brouillon

**Vérifier**:
- ✓ Items ajoutés correctement
- ✓ Calculs de remise justes
- ✓ TVA appliquée (20%)
- ✓ Total correct

---

### Étape 2.2 - Exporter Devis en PDF
**URL**: http://127.0.0.1:8000/quotes/{id}/export-pdf/

**Vérifier**:
- ✓ PDF généré sans erreur
- ✓ En-tête avec logo/info entreprise
- ✓ Détails devis (numéro, date, validité)
- ✓ Tableau articles avec prix/quantité
- ✓ Totaux (sous-total, remise, TVA, total)
- ✓ Conditions générales présentes
- ✓ Pied de page avec infos entreprise

---

### Étape 2.3 - Envoyer Devis par Email
**URL**: http://127.0.0.1:8000/quotes/{id}/send-email/

**Action**:
```
Email du client: contact@technopark.fr
Message personnalisé: "Veuillez trouver ci-joint notre devis numéro DEV-2026-001 pour validation."
Joindre PDF: ✓ Coché
```

**Vérifier**:
- ✓ Notification créée
- ✓ Status: "sent" après envoi
- ✓ Template email utilisé correctement

**Email vérifié dans Notifications**:
- URL: http://127.0.0.1:8000/notifications/
- ✓ Type: quote_sent
- ✓ Client: Technopark Inc
- ✓ Status: sent

---

### Étape 2.4 - Convertir Devis en Facture
**URL**: http://127.0.0.1:8000/quotes/{id}/convert-to-invoice/

**Attendu**:
- Nouvelle facture créée
- Numéro: INV-2026-001
- Articles copiés automatiquement
- Date: 12/05/2026
- Totaux identiques au devis
- Status de devis: "converted"
- Lien vers facture créée

**Vérifier**:
- ✓ Devis passé à "converted"
- ✓ Facture créée avec mêmes articles
- ✓ Montants identiques
- ✓ Relation facture-devis établie

---

### Étape 2.5 - Gérer la Facture
**URL**: http://127.0.0.1:8000/invoices/{id}/

**Détails affichés**:
- Numéro: INV-2026-001
- Client: Technopark Inc
- Date: 12/05/2026
- Articles avec prix
- Calculs TVA
- Montant total
- Statut paiement: "unpaid"

**Actions disponibles**:
- ✓ Bouton "Modifier"
- ✓ Bouton "Exporter PDF"
- ✓ Bouton "Envoyer Email"
- ✓ Bouton "Marquer comme archivée"
- ✓ Bouton "Voir archive logs"
- ✓ Bouton "Convertir devise" (NEW Tier 2)

---

### Étape 2.6 - Enregistrer un Paiement
**URL**: http://127.0.0.1:8000/invoices/{id}/add-payment/

**Action**:
```
Montant: 1848.00 EUR
Date Paiement: 12/05/2026
Méthode: Virement bancaire
Référence: ACME-DEV-2026-001
```

**Vérifier**:
- ✓ Paiement enregistré
- ✓ Invoice status: "paid"
- ✓ Montant payé: 1848.00
- ✓ Notification: "payment_received" créée

---

## 🎯 PARTIE 3: TIER 1 - EMAIL & NOTIFICATIONS

### Étape 3.1 - Vérifier Notifications
**URL**: http://127.0.0.1:8000/notifications/

**Filtrer par**:
- Type: quote_sent
- Status: sent
- Client: Technopark Inc

**Attendu**:
- Liste des notifications
- Colonnes: Type, Client, Status, Date envoi
- Détails email

**Vérifier**:
- ✓ quote_sent visible
- ✓ Status = "sent"
- ✓ Timestamp cohérent

---

### Étape 3.2 - Gérer Templates Email
**URL**: http://127.0.0.1:8000/email-templates/

**Vérifier les 6 templates**:
```
1. ✓ invoice_created
2. ✓ invoice_sent
3. ✓ invoice_reminder
4. ✓ quote_sent
5. ✓ quote_accepted
6. ✓ payment_thank_you
```

**Pour chaque template**:
- ✓ Subject visible
- ✓ Body avec variables {invoice_number}, {client_name}, etc.
- ✓ is_active checkbox
- ✓ Timestamps (created_at, updated_at)

---

### Étape 3.3 - Éditer un Template
**URL**: http://127.0.0.1:8000/email-templates/{id}/update/

**Template**: invoice_sent

**Modifier**:
```
Subject: "Votre facture {invoice_number} est prête"
Body: 
"Chère {client_name},

Veuillez trouver en pièce jointe votre facture {invoice_number}.

Montant à payer: {total} {currency}
Date d'échéance: {due_date}

Cordialement,
{company_name}"
```

**Vérifier**:
- ✓ Sauvegardé
- ✓ is_active = True
- ✓ Variables entre {}

---

## 🎯 PARTIE 4: TIER 1 - STATISTIQUES

### Étape 4.1 - Dashboard Statistiques
**URL**: http://127.0.0.1:8000/analytics/

**Vérifier les KPIs**:

1. **Chiffre d'affaires (Payé)**:
   - Montant: 1848.00 EUR
   - Badge vert ✓

2. **Chiffre d'affaires en attente**:
   - Montant: 0.00 EUR
   - Badge orange ✓

3. **Facture moyenne**:
   - Montant: 1848.00 EUR
   - Badge bleu ✓

4. **Factures en retard**:
   - Nombre: 0
   - Badge rouge ✓

5. **Taux de paiement**:
   - Pourcentage: 100%
   - Graphique ✓

---

### Étape 4.2 - Graphiques
**Attendu**:

**Graphique 1 - Revenus mensuels**:
- Axe X: Mois (mai 2026)
- Axe Y: Montants
- Courbe linéaire
- Valeur: 1848.00 EUR en mai

**Graphique 2 - Statuts paiement**:
- Doughnut chart
- Paid: 1 facture
- Unpaid: 0 factures
- Partially: 0 factures

**Vérifier**:
- ✓ Graphiques Chart.js chargés
- ✓ Données correctes
- ✓ Couleurs distinctes

---

### Étape 4.3 - Statistiques Détaillées
**Scroll down**:

**Top 10 Produits**:
- Consultation: 300 EUR (2 unités)
- Formation: 1200 EUR (1 unité)

**Top 10 Clients**:
- Technopark Inc: 1848.00 EUR

**Statistiques Devis**:
- Total: 1
- Acceptés: 0%
- Rejetés: 0%
- Conversion: 100%

**Autres KPIs**:
- Nouveaux clients: 3
- Valeur client moyenne: (1848/3) = 616.00 EUR
- Total remises: 150.00 EUR
- % remises: 8.1%

---

### Étape 4.4 - Filtrer par Période
**Contrôles**:
- Dropdown: "3 derniers mois" / "6 mois" / "12 mois" / "Tout"
- Bouton "Appliquer"

**Test**: Sélectionner "3 derniers mois"
- ✓ Graphiques mis à jour
- ✓ Statistiques recalculées
- ✓ Pas d'erreurs JavaScript

---

## 🎯 PARTIE 5: TIER 1 - AUDIT

### Étape 5.1 - Accéder Journal Audit
**URL**: http://127.0.0.1:8000/audit-log/

**Attendu**:
- Liste de tous les événements
- Pagination: 50 par page
- Colonnes: Timestamp, Action, Model, ID, User, IP

**Vérifier**:
- ✓ Les créations de clients
- ✓ Les créations de produits
- ✓ Les créations de devis/factures
- ✓ Les paiements

---

### Étape 5.2 - Filtrer l'Audit
**Filtres**:
```
Action: [create/update/delete/view] - Sélectionner "create"
Model: [Invoice/Quote/Client] - Sélectionner "Quote"
User: [Dropdown]
Date De: 10/05/2026
Date À: 14/05/2026
```

**Vérifier**:
- ✓ Filtre appliqué
- ✓ Seuls les devis créés affichés
- ✓ Pagination OK

---

### Étape 5.3 - Détails des Modifications
**Action**: Cliquer sur une ligne d'audit pour dérouler

**Attendu** (pour une création):
```
Action: create
Model: Quote
Objet: DEV-2026-001
User: (admin ou anonyme)
Timestamp: 12/05/2026 à HH:MM:SS
Old Values: {} (vide)
New Values: {
  "client": "Technopark Inc",
  "quote_number": "DEV-2026-001",
  "date": "2026-05-12",
  "total": "1848.00",
  ...
}
```

**Vérifier**:
- ✓ JSON avant/après visible
- ✓ Données complètes
- ✓ Formatage lisible

---

## 🎯 PARTIE 6: TIER 2 - MULTI-DEVISE

### Étape 6.1 - Configurer Taux de Change
**URL**: http://127.0.0.1:8000/exchange-rates/

**Ajouter taux**:
```
De (EUR):     EUR
Vers:         USD
Taux:         1.0850

De (EUR):     EUR
Vers:         GBP
Taux:         0.8634

De (USD):     USD
Vers:         GBP
Taux:         0.7955
```

**Vérifier**:
- ✓ Tableau mise à jour
- ✓ Dates affichées
- ✓ Taux corrects

---

### Étape 6.2 - Créer Devis avec USD
**URL**: http://127.0.0.1:8000/quotes/create/

**Devis 2**:
```
Client: Silicon Valley Corp
Devise: USD (NEW Tier 2)
Date: 12/05/2026
Date Validité: 09/06/2026
Articles:
  - Développement Django (10) @ 85 EUR = 850 EUR
  - Support Premium (1) @ 5000 EUR = 5000 EUR
Remise: 5%
TVA: 20%
```

**Attendu**:
- Numéro: DEV-2026-002
- Devise: USD (sélectable)
- Taux change: 1.0850
- Total USD: Calculé automatiquement

**Vérifier**:
- ✓ Devise USD sélectionnée
- ✓ Montant affichage EUR → USD
- ✓ Taux appliqué correctement

---

### Étape 6.3 - Convertir Devise (Facture)
**URL**: http://127.0.0.1:8000/invoices/{id}/convert-currency/

**Sur Facture EUR**:
- Montant actuel: 1848.00 EUR
- Convertir vers: GBP
- Taux: 0.8634

**Action**: Cliquer "Convertir"

**Vérifier**:
- ✓ Devise changée: GBP
- ✓ Montant recalculé: 1848 * 0.8634 ≈ 1595.22 GBP
- ✓ original_currency: EUR
- ✓ exchange_rate: 0.8634
- ✓ Audit log créé

---

### Étape 6.4 - Vérifier Admin Devise
**URL**: http://127.0.0.1:8000/admin/invoice_app/invoice/

**Cliquer sur une facture**:
- ✓ Section "Devise (Tier 2)" visible
- ✓ Champs affichés:
  - currency: EUR/USD/GBP
  - exchange_rate: 0.8634
  - original_currency: EUR

---

## 🎯 PARTIE 7: TIER 2 - RECHERCHE AVANCÉE

### Étape 7.1 - Accéder Recherche
**URL**: http://127.0.0.1:8000/search/

**Formulaire**:
- Texte: (TextInput)
- Type: [all/invoice/quote/client]
- Date de: (DateInput)
- Date à: (DateInput)
- Bouton: "Rechercher"

---

### Étape 7.2 - Rechercher par Texte
**Test 1 - Rechercher facture**:
```
Texte: "INV-2026-001"
Type: Tous les types
Rechercher
```

**Attendu**:
- ✓ Résultat: Facture INV-2026-001
- ✓ Client: Technopark Inc
- ✓ Date: 12/05/2026
- ✓ Montant: 1595.22 GBP
- ✓ Status: Paid

**Test 2 - Rechercher client**:
```
Texte: "Silicon Valley"
Type: Tous les types
Rechercher
```

**Attendu**:
- ✓ Résultat: Client Silicon Valley Corp
- ✓ Email: orders@silicon.us
- ✓ Pays: USA

---

### Étape 7.3 - Rechercher par Type & Date
**Test**:
```
Texte: ""
Type: Devis
Date de: 01/05/2026
Date à: 31/05/2026
Rechercher
```

**Attendu**:
- ✓ 2 devis affichés (DEV-2026-001, DEV-2026-002)
- ✓ Factures non affichées

---

### Étape 7.4 - Vérifier SearchIndex (Admin)
**URL**: http://127.0.0.1:8000/admin/invoice_app/searchindex/

**Vérifier**:
- ✓ Entrées pour chaque facture/devis/client
- ✓ content_type correct (invoice/quote/client)
- ✓ search_text rempli
- ✓ keywords rempli
- ✓ document_number présent
- ✓ client_name présent

---

## 🎯 PARTIE 8: TIER 2 - ARCHIVAGE

### Étape 8.1 - Archiver Facture
**URL**: http://127.0.0.1:8000/invoices/{id}/archive/

**Sur Facture INV-2026-001**:
```
Raison: "Paiement complet reçu, archivage pour compliance fiscale."
Bouton: Archiver
```

**Vérifier**:
- ✓ Facture marquée archivée
- ✓ is_archived = True
- ✓ archived_at = NOW
- ✓ archived_by = (utilisateur)
- ✓ ArchiveLog créé
- ✓ Audit log créé

---

### Étape 8.2 - Voir Factures Archivées
**URL**: http://127.0.0.1:8000/archived-invoices/

**Attendu**:
- ✓ INV-2026-001 dans la liste
- ✓ Colonnes: Numéro, Client, Date, Montant, Archivée le
- ✓ Boutons: "Voir", "Restaurer"
- ✓ Pagination si > 20

---

### Étape 8.3 - Voir Historique Archivage
**URL**: http://127.0.0.1:8000/invoices/{id}/archive-logs/

**Attendu**:
```
📦 Archivage
- Archivée par: (utilisateur)
- Date: 12/05/2026 HH:MM
- Raison: "Paiement complet reçu, archivage pour compliance fiscale."

Aucune restauration (pas encore restaurée)

Bouton: ↩️ Restaurer
```

**Vérifier**:
- ✓ Informations affichées
- ✓ Bouton Restaurer visible
- ✓ État: "Facture archivée"

---

### Étape 8.4 - Restaurer Facture
**URL**: http://127.0.0.1:8000/invoices/{id}/unarchive/

**Action**:
```
Raison de restauration: "Demande de client pour vérification comptable"
Bouton: Restaurer
```

**Vérifier**:
- ✓ Facture restaurée
- ✓ is_archived = False
- ✓ ArchiveLog mise à jour:
  - unarchived_by = (utilisateur)
  - unarchived_at = NOW
  - unarchive_reason = "Demande de client..."
- ✓ Audit log créé

---

### Étape 8.5 - Historique Archivage Complet
**URL**: http://127.0.0.1:8000/invoices/{id}/archive-logs/

**Attendu**:
```
État actuel: ✅ Facture active

📦 Archivage (Bloc 1)
- Archivée par: admin
- Date: 12/05/2026 21:55
- Raison: "Paiement complet reçu..."

↩️ Restauration (Bloc 2)
- Restaurée par: admin
- Date: 12/05/2026 21:56
- Raison: "Demande de client..."

Bouton: 📦 Archiver
```

**Vérifier**:
- ✓ Timeline complète affichée
- ✓ Les 2 blocs (archivage + restauration)
- ✓ Bouton archive au lieu d'unarchive

---

## 🎯 PARTIE 9: VALIDATION COMPLÈTE

### Étape 9.1 - Vérifier Admin Interface
**URL**: http://127.0.0.1:8000/admin/

**Login** (si nécessaire):
```
Username: admin
Password: (vous avez créé)
```

**Sections à vérifier**:
1. **Clients** (3 créés)
   - ✓ Technopark Inc
   - ✓ Silicon Valley Corp
   - ✓ London Financial Ltd

2. **Produits** (5 créés)
   - ✓ 5 produits visibles
   - ✓ Prix corrects

3. **Factures** (1 créée)
   - ✓ INV-2026-001
   - ✓ Devise: GBP
   - ✓ Amount: 1595.22
   - ✓ Status: Paid
   - ✓ is_archived: False (maintenant)

4. **Devis** (2 créés)
   - ✓ DEV-2026-001 (status: converted)
   - ✓ DEV-2026-002 (status: draft)

5. **Taux de Change** (3 ajoutés)
   - ✓ EUR→USD: 1.0850
   - ✓ EUR→GBP: 0.8634
   - ✓ USD→GBP: 0.7955

6. **Index Recherche**
   - ✓ Entrées pour factures/devis/clients

7. **Logs Archivage**
   - ✓ ArchiveLog pour INV-2026-001

8. **Notifications** (3+ créées)
   - ✓ quote_sent
   - ✓ payment_received
   - ✓ etc.

9. **Templates Email** (6 disponibles)
   - ✓ Tous les 6 types

10. **Journal Audit** (10+ entrées)
    - ✓ create, update actions
    - ✓ Tous les models

---

### Étape 9.2 - Test de Performance
**Vérifier**:
- ✓ Pages chargent < 1s
- ✓ Aucune erreur dans DevTools (F12)
- ✓ Pas de console.error
- ✓ CSS/JS chargeant correctement

---

### Étape 9.3 - Test PDF Export
**Créer Facture Supplémentaire**:
```
Client: London Financial Ltd
Articles: Support Premium (1) @ 5000 EUR
Devise: GBP
```

**Exporter PDF**: http://127.0.0.1:8000/invoices/{id}/export-pdf/

**Vérifier**:
- ✓ PDF généré
- ✓ En-tête avec logo/entreprise
- ✓ Numéro facture
- ✓ Devise GBP affichée
- ✓ Montant converti (5000 EUR * 0.8634 = 4317 GBP)
- ✓ Tableau articles
- ✓ Pied de page

---

## 📋 CHECKLIST FINALE

### Tier 1 - Enterprise Core Features
- [ ] ✅ Devis (CRUD + PDF + Conversion)
- [ ] ✅ Email & Notifications (9 types)
- [ ] ✅ Statistiques (15+ KPIs)
- [ ] ✅ Audit Trail (tous actions)

### Tier 2 - Advanced Features
- [ ] ✅ Multi-devise (EUR/USD/GBP)
- [ ] ✅ Taux de change (storage + lookup)
- [ ] ✅ Conversion devise (invoices)
- [ ] ✅ Recherche avancée (full-text)
- [ ] ✅ Archivage factures (archive + restore)
- [ ] ✅ Archive logs (historique complet)

### Technical
- [ ] ✅ Django check (0 issues)
- [ ] ✅ Server runs (no errors)
- [ ] ✅ DB migrations applied
- [ ] ✅ Admin functional
- [ ] ✅ URLs routing OK
- [ ] ✅ Templates responsive
- [ ] ✅ Forms validation

### Browser Testing
- [ ] ✅ All pages load
- [ ] ✅ No 404s/500s
- [ ] ✅ Forms submit correctly
- [ ] ✅ Charts render (Chart.js)
- [ ] ✅ PDFs generate
- [ ] ✅ Pagination works
- [ ] ✅ Filters functional

---

## 🎯 RÉSUMÉ FINAL

**Status**: ✅ **TOUS LES TESTS DOIVENT PASSER**

Si tous les points ci-dessus sont cochés ✓, l'application est **100% fonctionnelle** et prête pour:
- ✅ Production
- ✅ Déploiement
- ✅ Soutenance
- ✅ Documentation clients

**Serveur**: http://127.0.0.1:8000/  
**Admin**: http://127.0.0.1:8000/admin/  
**Date**: 12 mai 2026
