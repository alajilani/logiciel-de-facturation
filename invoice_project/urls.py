"""
URL configuration for invoice_project.
"""
from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def admin_logout_redirect(request):
    """Logout admin and redirect straight to the admin login with next=auth user list."""
    auth_logout(request)
    return redirect("/admin/login/?next=/admin/auth/user/")


urlpatterns = [
    path('admin/logout/', admin_logout_redirect, name='admin_logout_redirect'),
    path('admin/', admin.site.urls),
    path('', include('invoice_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
