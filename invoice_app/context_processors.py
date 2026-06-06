from .models import Notification


def notifications_context(request):
    """Expose notification counters/lists to all templates."""
    notifications = Notification.objects.filter(
        lu=False,
        niveau__in=['HAUTE', 'MOYENNE'],
    ).order_by('-date_creation')
    return {
        'navbar_unread_notifications_count': notifications.count(),
        'navbar_recent_notifications': notifications[:5],
    }
