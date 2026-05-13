#!/usr/bin/env python
"""Créer une notification de test"""

import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
django.setup()

from django.contrib.auth.models import User
from invoice_app.models import RealtimeNotification

print("🔧 Création d'une notification de test...\n")

# Récupérer l'utilisateur admin
admin_user = User.objects.get(username='admin')

# Créer une notification de test
notification = RealtimeNotification.objects.create(
    user=admin_user,
    notification_type='payment_received',
    title='💰 Paiement Reçu',
    message='Un paiement de 1500€ a été reçu de Acme Corp',
    priority='high',
    is_read=False,
    is_dismissed=False,
    action_url='/invoices/1/',
    expires_at=datetime.now() + timedelta(days=7)
)

print(f"✅ Notification créée avec succès!")
print(f"   ID: {notification.id}")
print(f"   Titre: {notification.title}")
print(f"   Type: {notification.get_notification_type_display()}")
print(f"   Priorité: {notification.get_priority_display()}")
print(f"   Utilisateur: {notification.user.username}")

print("\n🔗 Accédez à la page des notifications:")
print("   http://localhost:8000/notifications/")
