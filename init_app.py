#!/usr/bin/env python
"""Initialiser les utilisateurs et données de test"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
django.setup()

from django.contrib.auth.models import User
from invoice_app.models import Client, Product

print("🔧 Initialisation de l'application FactureApp...\n")

# 1. Créer un utilisateur de test
print("1️⃣  Création des utilisateurs...")
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@facturation.com', 'admin123')
    print("   ✅ Utilisateur admin créé (admin / admin123)")
else:
    print("   ℹ️  Utilisateur admin existe déjà")

if not User.objects.filter(username='demo').exists():
    demo_user = User.objects.create_user('demo', 'demo@facturation.com', 'demo123')
    print("   ✅ Utilisateur demo créé (demo / demo123)")
else:
    print("   ℹ️  Utilisateur demo existe déjà")

# 2. Afficher les utilisateurs
print("\n2️⃣  Utilisateurs disponibles:")
for user in User.objects.all():
    user_type = "👑 Superuser" if user.is_superuser else "👤 Regular user"
    print(f"   - {user.username} ({user.email}) - {user_type}")

# 3. Vérifier les données de test
print("\n3️⃣  Statistiques de base de données:")
print(f"   - Clients: {Client.objects.count()}")
print(f"   - Produits: {Product.objects.count()}")
print(f"   - Utilisateurs: {User.objects.count()}")

print("\n✨ Initialisation complétée!\n")
print("🚀 Vous pouvez maintenant accéder à l'application:")
print("   - URL: http://localhost:8000")
print("   - Admin: http://localhost:8000/admin")
print("   - Identifiants: admin / admin123")
