from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    CATEGORY_TYPES = [
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
    ]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='EXPENSE')
    icon = models.CharField(max_length=50, default='fa-tag', help_text='Font Awesome icon class name')
    color = models.CharField(max_length=20, default='#3b82f6', help_text='Hex color code for charts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_categories')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Expense(models.Model):
    PAYMENT_METHODS = [
        ('UPI', 'UPI / GPay / PhonePe'),
        ('CASH', 'Cash'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CREDIT_CARD', 'Credit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='expenses')
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='UPI')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.date})"


class Income(models.Model):
    PAYMENT_METHODS = [
        ('NET_BANKING', 'Bank Transfer / Salary'),
        ('UPI', 'UPI / Online'),
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='incomes')
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='NET_BANKING')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.date})"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField(default=timezone.now().month)
    year = models.IntegerField(default=timezone.now().year)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.category.name} Budget: ₹{self.monthly_limit} ({self.month}/{self.year})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency_symbol = models.CharField(max_length=5, default='₹')
    monthly_savings_goal = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
