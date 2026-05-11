"""Audit logging utilities"""
from django.http import HttpRequest
from .models import AuditLog
import json


def get_ip_address(request):
    """Get client IP address from request"""
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    return None


def get_changed_fields(old_obj, new_obj):
    """Compare old and new objects and return changed fields"""
    changed = {}
    
    if old_obj is None:
        # New object, all fields are "new"
        return None, {field.name: getattr(new_obj, field.name) for field in new_obj._meta.get_fields() 
                      if not field.many_to_one and field.name not in ['created_at', 'updated_at', 'id']}
    
    # Get all fields
    for field in new_obj._meta.get_fields():
        # Skip relations, timestamps, and ID
        if field.many_to_one or field.many_to_many or field.one_to_many:
            continue
        if field.name in ['id', 'created_at', 'updated_at']:
            continue
        
        try:
            old_value = getattr(old_obj, field.name)
            new_value = getattr(new_obj, field.name)
            
            # Convert to JSON-serializable format
            if hasattr(old_value, 'isoformat'):
                old_value = old_value.isoformat()
            if hasattr(new_value, 'isoformat'):
                new_value = new_value.isoformat()
            
            if str(old_value) != str(new_value):
                changed[field.name] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
        except:
            pass
    
    if not changed:
        return None, None
    
    return changed, None


def log_action(action, model, obj, request=None, old_obj=None):
    """
    Log an action to the audit trail
    
    Args:
        action: 'create', 'update', 'delete', or 'view'
        model: model class or string name
        obj: the object being logged (or None for delete)
        request: HTTP request (to get user and IP)
        old_obj: previous version of object (for updates)
    """
    try:
        # Get model name
        if isinstance(model, str):
            model_name = model
        else:
            model_name = model.__name__
        
        # Get object ID and string representation
        if obj:
            object_id = obj.pk
            object_str = str(obj)[:255]
        else:
            object_id = None
            object_str = None
        
        # Get user
        user = None
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        
        # Get IP address
        ip_address = get_ip_address(request) if request else None
        
        # Get changed fields
        old_values = {}
        new_values = {}
        
        if action == 'update' and obj and old_obj:
            changed, _ = get_changed_fields(old_obj, obj)
            if changed:
                for field, values in changed.items():
                    old_values[field] = values['old']
                    new_values[field] = values['new']
        elif action == 'create' and obj:
            for field in obj._meta.get_fields():
                if field.many_to_one or field.many_to_many or field.one_to_many:
                    continue
                if field.name in ['id', 'created_at', 'updated_at']:
                    continue
                try:
                    value = getattr(obj, field.name)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    new_values[field.name] = str(value)
                except:
                    pass
        
        # Create audit log entry
        AuditLog.objects.create(
            action=action,
            model=model_name,
            object_id=object_id or 0,
            object_str=object_str,
            user=user,
            ip_address=ip_address,
            old_values=old_values,
            new_values=new_values
        )
    except Exception as e:
        # Log error but don't break the application
        print(f"Audit logging error: {str(e)}")


def log_create(model, obj, request=None):
    """Log object creation"""
    log_action('create', model, obj, request)


def log_update(model, obj, request=None, old_obj=None):
    """Log object update"""
    log_action('update', model, obj, request, old_obj)


def log_delete(model, obj_id, obj_str, request=None):
    """Log object deletion"""
    log_action('delete', model, None, request)
