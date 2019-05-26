from django.db.models.signals import post_save, post_delete
from django.dispatch import Signal, receiver

from apps.storage_backends import delete_by_key

contact_registered = Signal(providing_args=["contact", "user"])


@receiver(post_delete, sender='users.User')
def clean_media_with_user_deletion(sender, instance, **kwargs):
    if instance.picture:
        delete_by_key(instance.picture.name)

