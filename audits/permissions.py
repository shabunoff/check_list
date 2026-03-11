from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def is_manager(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name='manager').exists()
        or user.groups.filter(name='leader').exists()
    )


def is_leader(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='leader').exists())


manager_required = user_passes_test(is_manager)
leader_required = user_passes_test(is_leader)


def ensure_leader(user):
    if not is_leader(user):
        raise PermissionDenied
