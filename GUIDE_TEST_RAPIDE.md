# 🚀 GUIDE TEST RAPIDE - 15 MINUTES

## ✅ STATUS SERVEUR
- **URL**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **Status**: ✅ EN LIGNE

---

## 📋 ÉTAPES DE TEST (5 min chacune)

### ✅ PARTIE 1: DASHBOARD (0-5 min)

**Cliquez sur**: http://127.0.0.1:8000/

**Vérifiez**:
- ✓ Logo "FactureApp" en haut
- ✓ Titre "Tableau de bord"
- ✓ 4 KPI cards (Clients, Factures, CA, En attente)
- ✓ Bouton "Nouvelle facture" bleu
- ✓ Section "Actions rapides" avec 3 boutons
- ✓ Tableau "Dernières factures"

---

### ✅ PARTIE 2: CRÉER UN CLIENT (5-10 min)

**Cliquez sur**: "Ajouter un client" OU http://127.0.0.1:8000/clients/create/

**Remplissez**:
```
Nom: Test Client SARL
Email: test@example.com
Téléphone: +33 1 23 45 67 89
Adresse livraison: 123 Rue Test, Paris
Adresse facturation: 123 Rue Test, Paris
Pays: France
```

**Cliquez**: "Créer" 

**Vérifiez**:
- ✓ Message de succès
- ✓ Redirection vers détail client
- ✓ Infos sauvegardées

---

### ✅ PARTIE 3: CRÉER UN PRODUIT (10-15 min)

**Cliquez sur**: "Ajouter un produit" OU http://127.0.0.1:8000/products/create/

**Remplissez**:
```
Nom: Service Test
Référence: SVC-001
Prix: 500.00
Description: Service de test
```

**Cliquez**: "Créer"

**Vérifiez**:
- ✓ Produit créé
- ✓ Prix affiché correctement

---

### ✅ PARTIE 4: CRÉER UNE FACTURE (15-25 min)

**Cliquez sur**: "Nouvelle facture" OU http://127.0.0.1:8000/invoices/create/

**Remplissez**:
```
Client: Test Client SARL
Date: 12/05/2026
Ajouter article:
  - Produit: Service Test
  - Quantité: 2
  - Prix unitaire: 500.00
  - Total: 1000.00
```

**Cliquez**: "Ajouter article" → "Créer facture"

**Vérifiez**:
- ✓ Numéro auto-généré (2026-00X)
- ✓ Articles affichés
- ✓ Total TVA: 1200.00 EUR
- ✓ Badge "⏱ En attente"

---

### ✅ PARTIE 5: EXPORTER PDF (25-30 min)

**Sur la facture** (http://127.0.0.1:8000/invoices/{id}/)

**Cliquez**: Bouton "Exporter PDF" (🖨️)

**Vérifiez**:
- ✓ PDF téléchargé
- ✓ En-tête avec infos entreprise
- ✓ Numéro facture visible
- ✓ Tableau articles complet
- ✓ Totaux corrects

---

### ✅ PARTIE 6: STATISTIQUES (30-35 min)

**Cliquez sur**: http://127.0.0.1:8000/analytics/

**Vérifiez**:
- ✓ 5 KPI cards au top
- ✓ Graphique linéaire (revenus)
- ✓ Graphique doughnut (statuts)
- ✓ Section "Top produits"
- ✓ Section "Top clients"

---

### ✅ PARTIE 7: TAUX DE CHANGE (35-40 min)

**Cliquez sur**: http://127.0.0.1:8000/exchange-rates/

**Ajoutez**:
```
De: EUR
Vers: USD
Taux: 1.0850
```

**Cliquez**: "Ajouter"

**Vérifiez**:
- ✓ Taux affiché dans le tableau
- ✓ Date présente
- ✓ Mise à jour visible

---

### ✅ PARTIE 8: RECHERCHE (40-45 min)

**Cliquez sur**: http://127.0.0.1:8000/search/

**Test 1 - Recherche facture**:
```
Texte: "2026-001" (ou numéro créé)
Type: Tous
Cliquez "Rechercher"
```

**Vérifiez**:
- ✓ Facture dans résultats
- ✓ Tableau avec détails
- ✓ Bouton "Voir" fonctionnel

---

### ✅ PARTIE 9: ARCHIVAGE (45-50 min)

**Allez sur votre facture**: http://127.0.0.1:8000/invoices/{id}/

**Cliquez**: "Archiver" (sous les actions)

**Remplissez**:
```
Raison: "Test archivage"
Cliquez: "Archiver"
```

**Vérifiez**:
- ✓ Facture archivée
- ✓ Redirection OK
- ✓ Bouton "Restaurer" visible

---

### ✅ PARTIE 10: ADMIN (50-55 min)

**Allez sur**: http://127.0.0.1:8000/admin/

**Vérifiez** (si login demandé):
```
Username: admin
Password: (votre mot de passe)
```

**Vérifiez**:
- ✓ Section Clients
- ✓ Section Factures
- ✓ Section Produits
- ✓ Section Taux de change
- ✓ Section Index recherche
- ✓ Section Archive logs

---

## 🎯 CHECKLIST FINALE

```
✓ Dashboard accessible
✓ Client créé
✓ Produit créé
✓ Facture créée
✓ PDF généré
✓ Statistiques visibles
✓ Taux change ajouté
✓ Recherche fonctionnelle
✓ Archivage OK
✓ Admin accessible
```

**Tous cochés?** ✅ **L'APP EST FONCTIONNELLE!**

---

## 🔗 LIENS RAPIDES

| Feature | URL |
|---------|-----|
| Dashboard | http://127.0.0.1:8000/ |
| Clients | http://127.0.0.1:8000/clients/ |
| Produits | http://127.0.0.1:8000/products/ |
| Factures | http://127.0.0.1:8000/invoices/ |
| Devis | http://127.0.0.1:8000/quotes/ |
| Statistiques | http://127.0.0.1:8000/analytics/ |
| Recherche | http://127.0.0.1:8000/search/ |
| Taux Change | http://127.0.0.1:8000/exchange-rates/ |
| Factures Archivées | http://127.0.0.1:8000/archived-invoices/ |
| Journal Audit | http://127.0.0.1:8000/audit-log/ |
| Notifications | http://127.0.0.1:8000/notifications/ |
| Admin | http://127.0.0.1:8000/admin/ |

---

## 📞 SUPPORT

**Erreurs?**
1. Vérifiez le terminal: `python manage.py check`
2. Vérifiez les migrations: `python manage.py showmigrations`
3. Vérifiez le serveur est actif: URL accessible?

**Succès?** ✅ Bravo! L'application est **100% opérationnelle**!
