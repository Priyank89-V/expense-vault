from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Category, Expense, Income, Budget, UserProfile


class ModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Food & Dining', category_type='EXPENSE', color='#ef4444')

    def test_category_creation(self):
        self.assertEqual(str(self.category), "Food & Dining (Expense)")

    def test_expense_creation(self):
        expense = Expense.objects.create(
            user=self.user,
            title='Groceries',
            amount=Decimal('450.00'),
            category=self.category,
            payment_method='UPI'
        )
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(expense.amount, Decimal('450.00'))

    def test_income_creation(self):
        inc_cat = Category.objects.create(name='Salary', category_type='INCOME')
        income = Income.objects.create(
            user=self.user,
            title='Monthly Stipend',
            amount=Decimal('15000.00'),
            category=inc_cat
        )
        self.assertEqual(Income.objects.count(), 1)
        self.assertEqual(income.amount, Decimal('15000.00'))

    def test_user_profile_signal(self):
        # UserProfile should be auto-created by post_save signal
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.currency_symbol, '₹')


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Tech', category_type='EXPENSE')

    def test_unauthenticated_dashboard_redirects(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_dashboard_access(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/dashboard.html')

    def test_add_expense_post(self):
        self.client.login(username='testuser', password='password123')
        post_data = {
            'title': 'Coffee',
            'amount': '120.00',
            'category': self.category.id,
            'date': timezone.now().date(),
            'payment_method': 'UPI',
            'description': 'Espresso'
        }
        response = self.client.post(reverse('add_expense'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_csv_export(self):
        self.client.login(username='testuser', password='password123')
        Expense.objects.create(
            user=self.user,
            title='Internet Bill',
            amount=Decimal('799.00'),
            category=self.category,
            payment_method='NET_BANKING'
        )
        response = self.client.get(reverse('export_expenses_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
