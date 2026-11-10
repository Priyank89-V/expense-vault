from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Expense, Income, Category, Budget, UserProfile


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create strong password'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        min_length=6
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. john_doe'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'payment_method', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Grocery shopping, Electricity bill'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes, invoice numbers, or details (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q
            # Filter categories: system default categories OR categories created by this user, type EXPENSE
            self.fields['category'].queryset = Category.objects.filter(
                category_type='EXPENSE'
            ).filter(Q(user=user) | Q(user__isnull=True))

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount



class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['title', 'amount', 'category', 'date', 'payment_method', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Salary, Freelance project, Dividend'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Income notes or details (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                category_type='INCOME'
            ).filter(Q(user=user) | Q(user__isnull=True))

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'monthly_limit', 'month', 'year']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'monthly_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5000.00', 'step': '0.01', 'min': '1'}),
            'month': forms.Select(attrs={'class': 'form-select'}, choices=[(i, f"{i:02d} - {timezone.datetime(2000, i, 1).strftime('%B')}") for i in range(1, 13)]),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2035'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                category_type='EXPENSE'
            ).filter(Q(user=user) | Q(user__isnull=True))


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Gym & Fitness'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. fa-dumbbell or fa-tag'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['currency_symbol', 'monthly_savings_goal', 'phone_number']
        widgets = {
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '₹ or $ or €'}),
            'monthly_savings_goal': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
        }
