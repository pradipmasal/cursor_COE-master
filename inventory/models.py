from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username

class Component(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate barcode if not provided
        if not self.barcode:
            # Get the next available ID or use count + 1
            next_id = Component.objects.count() + 1
            while True:
                barcode = f"COMP{next_id:06d}"
                if not Component.objects.filter(barcode=barcode).exists():
                    self.barcode = barcode
                    break
                next_id += 1
        super().save(*args, **kwargs)

class IssueRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    request_date = models.DateTimeField(auto_now_add=True)
    issue_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    return_deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_requests')
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = IssueRequest.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)
        
        # Update component quantity when status changes to approved or returned
        if self.status == 'approved' and (is_new or old_status != 'approved'):
            self.component.quantity -= self.quantity
            if self.component.quantity <= 0:
                self.component.available = False
            self.component.save()
        elif self.status == 'returned' and old_status != 'returned':
            self.component.quantity += self.quantity
            self.component.available = True
            self.component.save()
    
    @property
    def is_overdue(self):
        if self.status == 'approved' and self.return_deadline:
            return timezone.now() > self.return_deadline
        return False
    
    @property
    def days_remaining(self):
        if self.status == 'approved' and self.return_deadline:
            remaining = self.return_deadline - timezone.now()
            return remaining.days
        return 0

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
