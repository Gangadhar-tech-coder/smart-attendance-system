# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import StudentProfile
# User = settings.AUTH_USER_MODEL

# @receiver(post_save, sender=User)
# def create_student_profile(sender, instance, created, **kwargs):
#     if created:
#         StudentProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_student_profile(sender, instance, **kwargs):
#     instance.student_profile.save()