"""FactureApp — Configuration de l'espace /admin/.

Espace de pilotage SYSTÈME uniquement :
- configuration entreprise / facturation
- gestion des utilisateurs & rôles
- supervision (audit)
- maintenance technique

Les modules métier (clients, produits, factures, paiements, devis) sont gérés
dans l'espace comptable et ne sont volontairement pas exposés ici.
"""

import csv
import io
import os
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.management import call_command
from django.db import connection
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from .models import AuditLog, Client, CompanyInfo, Invoice, Notification, Payment, Product



# =============================================================================
# Branding global
# =============================================================================
admin.site.site_header = "Numa Console"
admin.site.site_title = "Numa Console"
admin.site.index_title = "Tableau de bord administrateur"


# =============================================================================
# Helpers
# =============================================================================
def _badge(text, color="muted"):
    return format_html(
        '<span class="ab-badge ab-badge-{}">{}</span>', color, text
    )


# =============================================================================
# Utilisateurs — rôles métier abstraits (Administrateur / Comptable)
# =============================================================================
ROLE_ADMIN = "ADMIN"
ROLE_COMPTABLE = "COMPTABLE"
ROLE_CHOICES = [
    (ROLE_ADMIN, "Administrateur — accès complet à la plateforme"),
    (ROLE_COMPTABLE, "Comptable — gestion clients, factures, paiements, devis, stock"),
]


def _get_role(user):
    if user.is_superuser or user.groups.filter(name__iexact="Administrateur").exists():
        return ROLE_ADMIN
    return ROLE_COMPTABLE


def _apply_role(user, role):
    admin_group, _ = Group.objects.get_or_create(name="Administrateur")
    comptable_group, _ = Group.objects.get_or_create(name="Comptable")
    user.groups.remove(admin_group, comptable_group)
    if role == ROLE_ADMIN:
        user.is_staff = True
        user.is_superuser = True
        user.groups.add(admin_group)
    else:
        user.is_staff = True   # nécessaire pour accéder à l'espace comptable Django
        user.is_superuser = False
        user.groups.add(comptable_group)
    user.save()


class SimpleUserChangeForm(UserChangeForm):
    """Formulaire utilisateur sans hash mot de passe ni permissions techniques."""
    password = None
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Rôle",
        required=True,
        help_text="Le rôle détermine automatiquement les permissions.",
    )

    class Meta(UserChangeForm.Meta):
        fields = ("username", "first_name", "last_name", "email", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["role"].initial = _get_role(self.instance)


class SimpleUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, label="Rôle", initial=ROLE_COMPTABLE,
    )
    email = forms.EmailField(required=True, label="Adresse email")
    first_name = forms.CharField(required=False, label="Prénom")
    last_name = forms.CharField(required=False, label="Nom")

    class Meta(UserCreationForm.Meta):
        fields = ("username", "first_name", "last_name", "email")


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = SimpleUserChangeForm
    add_form = SimpleUserCreationForm

    list_display = (
        "username",
        "email",
        "nom_complet",
        "role_badge",
        "is_active_badge",
        "last_login_fmt",
        "date_joined_fmt",
        "actions_col",
    )
    list_filter = ("is_active",)
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    list_per_page = 25
    actions = ["activer_utilisateurs", "desactiver_utilisateurs"]

    # On supprime totalement les widgets de permissions techniques.
    filter_horizontal = ()
    readonly_fields = ("last_login", "date_joined", "password_actions")

    fieldsets = (
        ("Informations générales", {
            "fields": ("username", "first_name", "last_name", "email"),
        }),
        ("Accès", {
            "fields": ("role", "is_active"),
            "description": "Le rôle détermine les permissions de manière automatique.",
        }),
        ("Sécurité", {
            "fields": ("password_actions", "last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        ("Informations générales", {
            "fields": ("username", "first_name", "last_name", "email"),
        }),
        ("Accès", {
            "fields": ("role",),
        }),
        ("Mot de passe", {
            "fields": ("password1", "password2"),
        }),
    )

    # ---- Colonnes de liste --------------------------------------------------
    @admin.display(description="Nom complet")
    def nom_complet(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or "—"

    @admin.display(description="Rôle")
    def role_badge(self, obj):
        role = _get_role(obj)
        if role == ROLE_ADMIN:
            return _badge("Administrateur", "danger")
        return _badge("Comptable", "info")

    @admin.display(description="Statut", boolean=False)
    def is_active_badge(self, obj):
        return _badge("Actif", "success") if obj.is_active else _badge("Inactif", "muted")

    @admin.display(description="Dernière connexion", ordering="last_login")
    def last_login_fmt(self, obj):
        return obj.last_login.strftime("%d/%m/%Y %H:%M") if obj.last_login else "—"

    @admin.display(description="Inscrit le", ordering="date_joined")
    def date_joined_fmt(self, obj):
        return obj.date_joined.strftime("%d/%m/%Y") if obj.date_joined else "—"

    @admin.display(description="Actions")
    def actions_col(self, obj):
        change_url = reverse("admin:auth_user_change", args=[obj.pk])
        pwd_url = reverse("admin:auth_user_password_change", args=[obj.pk])
        return format_html(
            '<a class="ab-link" href="{}"><i class="bi bi-pencil"></i></a> '
            '&nbsp;<a class="ab-link" href="{}" title="Changer mot de passe">'
            '<i class="bi bi-key"></i></a>',
            change_url, pwd_url,
        )

    # ---- Champ "Sécurité" : actions mot de passe ---------------------------
    @admin.display(description="Mot de passe")
    def password_actions(self, obj):
        if not obj or not obj.pk:
            return "—"
        url = reverse("admin:auth_user_password_change", args=[obj.pk])
        return format_html(
            '<a class="ab-btn ab-btn-primary" href="{}">'
            '<i class="bi bi-key"></i> Changer / réinitialiser le mot de passe</a>',
            url,
        )

    # ---- Sauvegarde : appliquer le rôle métier -----------------------------
    def save_model(self, request, obj, form, change):
        # Initialiser is_staff côté création pour permettre l'enregistrement.
        if not change:
            obj.is_staff = True
        super().save_model(request, obj, form, change)
        role = form.cleaned_data.get("role")
        if role:
            _apply_role(obj, role)

    # ---- Actions ------------------------------------------------------------
    @admin.action(description="Activer les utilisateurs sélectionnés")
    def activer_utilisateurs(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} utilisateur(s) activé(s).")

    @admin.action(description="Désactiver les utilisateurs sélectionnés")
    def desactiver_utilisateurs(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f"{n} utilisateur(s) désactivé(s).")


# =============================================================================
# Groupes (rôles métier) — affichage simplifié
# =============================================================================
admin.site.unregister(Group)


@admin.register(Group)
class SimpleGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description_role", "nb_utilisateurs")
    search_fields = ("name",)
    fields = ("name",)  # On masque le widget de permissions techniques.

    @admin.display(description="Description")
    def description_role(self, obj):
        descriptions = {
            "administrateur": "Accès complet à la plateforme et à la configuration système.",
            "comptable": "Gestion clients, factures, paiements, devis et stock.",
        }
        return descriptions.get(obj.name.lower(), "Rôle personnalisé.")

    @admin.display(description="Utilisateurs")
    def nb_utilisateurs(self, obj):
        return obj.user_set.count()


# =============================================================================
# Informations entreprise — singleton SaaS
# =============================================================================
class CompanyInfoForm(forms.ModelForm):
    CURRENCY_CHOICES = [
        ("EUR", "Euro (€)"),
        ("USD", "Dollar US ($)"),
        ("MAD", "Dirham marocain (DH)"),
    ]

    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label="Devise",
        widget=forms.Select(attrs={"class": "ab-input"}),
    )

    class Meta:
        model = CompanyInfo
        fields = "__all__"
        labels = {
            "name": "Nom de l'entreprise",
            "logo": "Logo de l'entreprise",
            "country": "Pays",
            "address": "Adresse",
            "postal_code": "Code postal",
            "city": "Ville",
            "phone": "Téléphone",
            "email": "Adresse email",
            "website": "Site web",
            "siret": "SIRET",
            "siren": "SIREN",
            "tva_number": "Numéro TVA intracommunautaire",
            "invoice_prefix": "Préfixe facture",
            "default_tva": "TVA par défaut (%)",
            "default_payment_terms": "Conditions de paiement par défaut",
            "default_legal_mentions": "Mentions légales par défaut",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "default_legal_mentions": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Le nom de l'entreprise est obligatoire.")
        return name

    def clean_siret(self):
        siret = (self.cleaned_data.get("siret") or "").replace(" ", "")
        if siret and (not siret.isdigit() or len(siret) != 14):
            raise forms.ValidationError("Le SIRET doit contenir exactement 14 chiffres.")
        return siret or None

    def clean_siren(self):
        siren = (self.cleaned_data.get("siren") or "").replace(" ", "")
        if siren and (not siren.isdigit() or len(siren) != 9):
            raise forms.ValidationError("Le SIREN doit contenir exactement 9 chiffres.")
        return siren or None

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if phone:
            cleaned = phone.replace(" ", "").replace(".", "").replace("-", "").replace("+", "")
            if not cleaned.isdigit() or len(cleaned) < 6:
                raise forms.ValidationError("Numéro de téléphone invalide.")
        return phone or None


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    form = CompanyInfoForm
    actions = None
    search_fields = ()
    save_on_top = False
    change_form_template = "admin/invoice_app/companyinfo/change_form.html"

    def has_add_permission(self, request):
        return not CompanyInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = CompanyInfo.objects.first()
        if obj:
            return HttpResponseRedirect(
                reverse("admin:invoice_app_companyinfo_change", args=[obj.pk])
            )
        return HttpResponseRedirect(reverse("admin:invoice_app_companyinfo_add"))


# =============================================================================
# Journaux d'audit (lecture seule)
# =============================================================================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action_badge", "model", "object_str", "user", "ip_address")
    list_filter = ("action", "model")
    search_fields = ("object_str", "user", "ip_address")
    ordering = ("-timestamp",)
    readonly_fields = (
        "action", "model", "object_id", "object_str",
        "user", "ip_address", "old_values", "new_values", "timestamp",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Action", ordering="action")
    def action_badge(self, obj):
        colors = {"create": "success", "update": "info", "delete": "danger", "view": "muted"}
        return _badge(obj.get_action_display(), colors.get(obj.action, "muted"))


# =============================================================================
# Centre système — supervision, sauvegardes, exports, maintenance
# =============================================================================
_BACKUP_CACHE_KEY = "system:last_backup"


def _check_db_status():
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
            c.fetchone()
        vendor = (connection.vendor or "db").upper()
        name = connection.settings_dict.get("NAME", "")
        if name:
            return True, f"{vendor} · {name}"
        return True, vendor
    except Exception as e:
        return False, str(e)[:80]


def _check_smtp_status():
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "console" in backend:
        return "warning", "Mode console (dev)"
    if not getattr(settings, "EMAIL_HOST_USER", None):
        return "warning", "À configurer"
    return "ok", "Opérationnel"


def _media_size_mb():
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if not media_root or not os.path.isdir(media_root):
        return 0.0
    total = 0
    for dirpath, _, filenames in os.walk(media_root):
        for f in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return round(total / (1024 * 1024), 2)


def _last_backup_info():
    info = cache.get(_BACKUP_CACHE_KEY)
    if not info:
        return None
    return info


def _set_last_backup(kind):
    cache.set(
        _BACKUP_CACHE_KEY,
        {"kind": kind, "at": timezone.now()},
        timeout=60 * 60 * 24 * 365,
    )


def _system_context(request):
    db_ok, db_msg = _check_db_status()
    smtp_state, smtp_msg = _check_smtp_status()
    last_backup = _last_backup_info()

    overdue = Invoice.objects.filter(statut="EN_RETARD").count()
    low_stock = Product.objects.filter(
        type_item="PRODUIT", suivre_stock=True, stock__lte=F("seuil_alerte"),
    ).count() if hasattr(Product, "type_item") else 0
    unpaid = Invoice.objects.exclude(statut__in=["PAYEE", "ANNULEE"]).count()
    active_alerts = overdue + low_stock

    # Activité récente : ignorer les objets de test évidents (chaînes très courtes
    # ou répétition d'un même caractère, type "gggg", "aaaa", "test", ...)
    _junk = {"test", "tttt", "gggg", "aaaa", "azer", "qsdf", "wxcv", "abc", "xxx"}
    recent_qs = AuditLog.objects.order_by("-timestamp")[:30]
    recent = []
    for log in recent_qs:
        s = (log.object_str or "").strip().lower()
        if not s:
            recent.append(log)
        elif s in _junk:
            continue
        elif len(s) <= 5 and len(set(s)) == 1:
            continue
        else:
            recent.append(log)
        if len(recent) >= 5:
            break

    return {
        "title": "Centre système",
        "status": {
            "db_ok": db_ok,
            "db_msg": db_msg,
            "smtp_state": smtp_state,  # "ok" | "warning"
            "smtp_msg": smtp_msg,
            "last_backup": last_backup,  # {kind, at} | None
            "storage_mb": _media_size_mb(),
            "active_alerts": active_alerts,
            "overdue": overdue,
            "low_stock": low_stock,
            "unpaid": unpaid,
        },
        "recent_audit": recent,
    }


def _system_view(request):
    if not request.user.is_active or not request.user.is_staff:
        return HttpResponseRedirect(reverse("admin:login"))
    context = {**admin.site.each_context(request), **_system_context(request)}
    return TemplateResponse(request, "admin/system.html", context)


# ---------- Exports CSV ------------------------------------------------------
def _csv_response(filename, header, rows):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    resp = HttpResponse(
        "\ufeff" + buf.getvalue(),
        content_type="text/csv; charset=utf-8",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def _export_clients(request):
    rows = Client.objects.all().values_list(
        "id", "type_client", "nom", "raison_sociale", "email", "telephone",
        "ville_facturation", "pays_facturation", "statut", "created_at",
    )
    return _csv_response(
        f"clients_{timezone.now():%Y%m%d_%H%M}.csv",
        ["ID", "Type", "Nom", "Raison sociale", "Email", "Téléphone",
         "Ville", "Pays", "Statut", "Créé le"],
        rows,
    )


def _export_invoices(request):
    rows = Invoice.objects.select_related("client").values_list(
        "invoice_number", "client__nom", "date", "due_date", "statut",
        "total_ht", "total_tva", "total_ttc", "amount_paid", "payment_method",
    )
    return _csv_response(
        f"factures_{timezone.now():%Y%m%d_%H%M}.csv",
        ["Numéro", "Client", "Date", "Échéance", "Statut",
         "Total HT", "TVA", "Total TTC", "Payé", "Mode de règlement"],
        rows,
    )


def _export_payments(request):
    rows = Payment.objects.select_related("invoice", "invoice__client").values_list(
        "id", "invoice__invoice_number", "invoice__client__nom",
        "payment_date", "amount", "payment_method", "reference",
    )
    return _csv_response(
        f"paiements_{timezone.now():%Y%m%d_%H%M}.csv",
        ["ID", "Facture", "Client", "Date", "Montant", "Méthode", "Référence"],
        rows,
    )


def _export_audit(request):
    rows = AuditLog.objects.values_list(
        "timestamp", "action", "model", "object_str", "user", "ip_address",
    )
    return _csv_response(
        f"audit_{timezone.now():%Y%m%d_%H%M}.csv",
        ["Date", "Action", "Modèle", "Objet", "Utilisateur", "IP"],
        rows,
    )


def _export_db_json(request):
    """Sauvegarde portable de la base via Django dumpdata."""
    buf = io.StringIO()
    call_command(
        "dumpdata",
        "--natural-foreign", "--natural-primary",
        "--exclude", "contenttypes",
        "--exclude", "auth.Permission",
        "--indent", "2",
        stdout=buf,
    )
    _set_last_backup("Base de données (JSON)")
    resp = HttpResponse(buf.getvalue(), content_type="application/json")
    resp["Content-Disposition"] = (
        f'attachment; filename="db_backup_{timezone.now():%Y%m%d_%H%M}.json"'
    )
    return resp


def _export_archive(request):
    """Archive ZIP : dump base + tous les CSV."""
    import zipfile
    mem = io.BytesIO()
    ts = timezone.now().strftime("%Y%m%d_%H%M")
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        # dump DB JSON
        db_buf = io.StringIO()
        call_command(
            "dumpdata",
            "--natural-foreign", "--natural-primary",
            "--exclude", "contenttypes",
            "--exclude", "auth.Permission",
            "--indent", "2",
            stdout=db_buf,
        )
        zf.writestr(f"db_backup_{ts}.json", db_buf.getvalue())

        # CSV exports
        for name, exporter in [
            ("clients", _export_clients),
            ("factures", _export_invoices),
            ("paiements", _export_payments),
            ("audit", _export_audit),
        ]:
            resp = exporter(request)
            zf.writestr(f"{name}_{ts}.csv", resp.content)
    _set_last_backup("Archive complète (ZIP)")
    resp = HttpResponse(mem.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="numa_backup_{ts}.zip"'
    return resp


# ---------- Actions de maintenance (POST) ------------------------------------
def _redirect_panel(request, level, msg):
    getattr(messages, level)(request, msg)
    return HttpResponseRedirect(reverse("admin:system_panel"))


@require_POST
def _action_check_low_stock(request):
    try:
        n = Product.objects.filter(
            type_item="PRODUIT", suivre_stock=True, stock__lte=F("seuil_alerte"),
        ).count()
        return _redirect_panel(request, "success", f"Vérification stock effectuée : {n} produit(s) sous le seuil.")
    except Exception as e:
        return _redirect_panel(request, "error", f"Erreur lors de la vérification : {e}")


@require_POST
def _action_recompute_stats(request):
    """Recalcule les statuts EN_RETARD selon la date d'échéance."""
    try:
        today = timezone.now().date()
        updated = Invoice.objects.filter(
            due_date__lt=today,
        ).exclude(statut__in=["PAYEE", "ANNULEE", "EN_RETARD"]).update(statut="EN_RETARD")
        if updated:
            return _redirect_panel(request, "success", f"Statuts mis à jour : {updated} facture(s) passée(s) en retard.")
        return _redirect_panel(request, "info", "Statuts à jour. Aucune facture en retard détectée.")
    except Exception as e:
        return _redirect_panel(request, "error", f"Erreur : {e}")


@require_POST
def _action_clean_notifications(request):
    try:
        cutoff = timezone.now() - timedelta(days=90)
        # Notification possède un champ created_at ou date_creation selon le modèle
        date_field = "date_creation" if hasattr(Notification, "date_creation") else "created_at"
        deleted, _ = Notification.objects.filter(**{f"{date_field}__lt": cutoff}).delete()
        return _redirect_panel(request, "success", f"{deleted} notification(s) de plus de 90 jours supprimée(s).")
    except Exception as e:
        return _redirect_panel(request, "error", f"Erreur : {e}")


@require_POST
def _action_clean_logs(request):
    try:
        cutoff = timezone.now() - timedelta(days=365)
        deleted, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
        return _redirect_panel(request, "success", f"{deleted} journal(aux) de plus de 365 jours supprimé(s).")
    except Exception as e:
        return _redirect_panel(request, "error", f"Erreur : {e}")


@require_POST
def _action_test_smtp(request):
    to_email = request.user.email
    if not to_email:
        return _redirect_panel(request, "warning", "Votre compte n'a pas d'adresse email. Renseignez-la pour tester l'envoi SMTP.")
    try:
        send_mail(
            subject="[Numa] Test SMTP",
            message="Ceci est un email de test envoyé depuis le Centre système Numa.",
            from_email=None,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return _redirect_panel(request, "success", f"Email de test envoyé à {to_email}.")
    except Exception as e:
        return _redirect_panel(request, "error", f"Échec d'envoi SMTP : {e}")


@require_POST
def _action_clear_cache(request):
    try:
        cache.clear()
        return _redirect_panel(request, "success", "Cache applicatif vidé.")
    except Exception as e:
        return _redirect_panel(request, "error", f"Erreur : {e}")


# ---------- Wiring URLs ------------------------------------------------------
def _staff_only(view):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            return HttpResponseRedirect(reverse("admin:login"))
        return view(request, *args, **kwargs)
    return wrapped


_original_get_urls = admin.site.get_urls


def _custom_get_urls():
    custom = [
        path("systeme/", admin.site.admin_view(_system_view), name="system_panel"),

        # Exports CSV / archive
        path("systeme/export/clients/",
             admin.site.admin_view(_export_clients), name="system_export_clients"),
        path("systeme/export/factures/",
             admin.site.admin_view(_export_invoices), name="system_export_invoices"),
        path("systeme/export/paiements/",
             admin.site.admin_view(_export_payments), name="system_export_payments"),
        path("systeme/export/audit/",
             admin.site.admin_view(_export_audit), name="system_export_audit"),
        path("systeme/export/base/",
             admin.site.admin_view(_export_db_json), name="system_export_db"),
        path("systeme/export/archive/",
             admin.site.admin_view(_export_archive), name="system_export_archive"),

        # Actions de maintenance (POST)
        path("systeme/action/recompute-stats/",
             admin.site.admin_view(_action_recompute_stats), name="system_action_recompute_stats"),
        path("systeme/action/check-low-stock/",
             admin.site.admin_view(_action_check_low_stock), name="system_action_check_low_stock"),
        path("systeme/action/clean-notifications/",
             admin.site.admin_view(_action_clean_notifications), name="system_action_clean_notifications"),
        path("systeme/action/clean-logs/",
             admin.site.admin_view(_action_clean_logs), name="system_action_clean_logs"),
        path("systeme/action/test-smtp/",
             admin.site.admin_view(_action_test_smtp), name="system_action_test_smtp"),
        path("systeme/action/clear-cache/",
             admin.site.admin_view(_action_clear_cache), name="system_action_clear_cache"),
    ]
    return custom + _original_get_urls()


admin.site.get_urls = _custom_get_urls

