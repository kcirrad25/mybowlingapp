from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .audit import get_current_user
from .models import AuditLog, BowlerScore, TeamScore

TRACKED_FIELDS = ("game1", "game2", "game3", "handicap", "scratch_total", "total_with_handicap")


def _snapshot(instance):
    return {field: getattr(instance, field) for field in TRACKED_FIELDS}


def _diff(old_snapshot, new_snapshot):
    changes = {}
    for field in TRACKED_FIELDS:
        old_value = old_snapshot.get(field) if old_snapshot else None
        new_value = new_snapshot.get(field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}
    return changes


def _create_audit_entry(instance, action, changed_fields):
    AuditLog.objects.create(
        actor=get_current_user(),
        action=action,
        model_name=instance.__class__.__name__,
        object_pk=str(instance.pk),
        object_repr=str(instance),
        changed_fields=changed_fields,
    )


@receiver(pre_save, sender=BowlerScore)
@receiver(pre_save, sender=TeamScore)
def capture_pre_save_snapshot(sender, instance, **kwargs):
    if not instance.pk:
        instance._audit_snapshot = None
        return
    previous = sender.objects.filter(pk=instance.pk).first()
    instance._audit_snapshot = _snapshot(previous) if previous else None


@receiver(post_save, sender=BowlerScore)
@receiver(post_save, sender=TeamScore)
def log_score_save(sender, instance, created, **kwargs):
    new_snapshot = _snapshot(instance)
    old_snapshot = getattr(instance, "_audit_snapshot", None)
    action = AuditLog.Action.CREATED if created else AuditLog.Action.UPDATED
    changes = _diff(old_snapshot, new_snapshot) if not created else {field: {"old": None, "new": value} for field, value in new_snapshot.items()}
    _create_audit_entry(instance, action, changes)


@receiver(post_delete, sender=BowlerScore)
@receiver(post_delete, sender=TeamScore)
def log_score_delete(sender, instance, **kwargs):
    _create_audit_entry(
        instance,
        AuditLog.Action.DELETED,
        {field: {"old": getattr(instance, field), "new": None} for field in TRACKED_FIELDS},
    )
