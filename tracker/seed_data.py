import random
from decimal import Decimal
from datetime import date, timedelta
from .models import Category, Expense, Income, Budget


DEFAULT_EXPENSE_CATEGORIES = [
    {'name': 'Food & Dining', 'icon': 'fa-utensils', 'color': '#ef4444'},
    {'name': 'Rent & Housing', 'icon': 'fa-house', 'color': '#3b82f6'},
    {'name': 'Groceries & Supplies', 'icon': 'fa-cart-shopping', 'color': '#10b981'},
    {'name': 'Transportation & Fuel', 'icon': 'fa-car', 'color': '#f59e0b'},
    {'name': 'Utilities & Bills', 'icon': 'fa-bolt', 'color': '#8b5cf6'},
    {'name': 'Entertainment & Subscriptions', 'icon': 'fa-film', 'color': '#ec4899'},
    {'name': 'Healthcare & Pharmacy', 'icon': 'fa-heart-pulse', 'color': '#06b6d4'},
    {'name': 'Shopping & Clothing', 'icon': 'fa-bag-shopping', 'color': '#6366f1'},
    {'name': 'Education & Courses', 'icon': 'fa-graduation-cap', 'color': '#14b8a6'},
]

DEFAULT_INCOME_CATEGORIES = [
    {'name': 'Monthly Salary', 'icon': 'fa-money-bill-wave', 'color': '#10b981'},
    {'name': 'Freelance & Projects', 'icon': 'fa-laptop-code', 'color': '#3b82f6'},
    {'name': 'Investments & Dividends', 'icon': 'fa-chart-line', 'color': '#8b5cf6'},
    {'name': 'Scholarship / Allowance', 'icon': 'fa-gift', 'color': '#f59e0b'},
]


def ensure_default_categories():
    for item in DEFAULT_EXPENSE_CATEGORIES:
        Category.objects.get_or_create(
            name=item['name'],
            category_type='EXPENSE',
            defaults={
                'icon': item['icon'],
                'color': item['color'],
                'is_default': True
            }
        )
    for item in DEFAULT_INCOME_CATEGORIES:
        Category.objects.get_or_create(
            name=item['name'],
            category_type='INCOME',
            defaults={
                'icon': item['icon'],
                'color': item['color'],
                'is_default': True
            }
        )


def populate_sample_data(user):
    ensure_default_categories()

    today = date.today()
    curr_month = today.month
    curr_year = today.year

    # Add Budgets for current month
    food_cat = Category.objects.filter(name='Food & Dining', category_type='EXPENSE').first()
    groceries_cat = Category.objects.filter(name='Groceries & Supplies', category_type='EXPENSE').first()
    transport_cat = Category.objects.filter(name='Transportation & Fuel', category_type='EXPENSE').first()
    ent_cat = Category.objects.filter(name='Entertainment & Subscriptions', category_type='EXPENSE').first()
    bills_cat = Category.objects.filter(name='Utilities & Bills', category_type='EXPENSE').first()

    if food_cat:
        Budget.objects.update_or_create(user=user, category=food_cat, month=curr_month, year=curr_year, defaults={'monthly_limit': Decimal('6000.00')})
    if groceries_cat:
        Budget.objects.update_or_create(user=user, category=groceries_cat, month=curr_month, year=curr_year, defaults={'monthly_limit': Decimal('4500.00')})
    if transport_cat:
        Budget.objects.update_or_create(user=user, category=transport_cat, month=curr_month, year=curr_year, defaults={'monthly_limit': Decimal('3000.00')})
    if ent_cat:
        Budget.objects.update_or_create(user=user, category=ent_cat, month=curr_month, year=curr_year, defaults={'monthly_limit': Decimal('2000.00')})

    # Sample Incomes for current month & past months
    salary_cat = Category.objects.filter(name='Monthly Salary', category_type='INCOME').first()
    freelance_cat = Category.objects.filter(name='Freelance & Projects', category_type='INCOME').first()

    sample_incomes = [
        {'title': 'Primary Job Salary', 'amount': Decimal('45000.00'), 'category': salary_cat, 'date': today.replace(day=1), 'payment_method': 'NET_BANKING', 'desc': 'Direct corporate deposit'},
        {'title': 'UI Design Freelance Gig', 'amount': Decimal('8500.00'), 'category': freelance_cat, 'date': max(today.replace(day=10), today - timedelta(days=5)), 'payment_method': 'UPI', 'desc': 'Client landing page payment'},
    ]

    for item in sample_incomes:
        Income.objects.create(
            user=user,
            title=item['title'],
            amount=item['amount'],
            category=item['category'],
            date=item['date'],
            payment_method=item['payment_method'],
            description=item['desc']
        )

    # Sample Expenses
    sample_expenses = [
        {'title': 'Apartment Rent', 'amount': Decimal('12000.00'), 'category': Category.objects.filter(name='Rent & Housing').first(), 'days_ago': 14, 'pm': 'NET_BANKING'},
        {'title': 'Supermarket Groceries', 'amount': Decimal('2350.00'), 'category': groceries_cat, 'days_ago': 12, 'pm': 'UPI'},
        {'title': 'Electricity & Water Bill', 'amount': Decimal('1450.00'), 'category': bills_cat, 'days_ago': 10, 'pm': 'UPI'},
        {'title': 'Weekend Team Dinner', 'amount': Decimal('1820.00'), 'category': food_cat, 'days_ago': 8, 'pm': 'CREDIT_CARD'},
        {'title': 'Fuel / Metro Recharge', 'amount': Decimal('800.00'), 'category': transport_cat, 'days_ago': 6, 'pm': 'UPI'},
        {'title': 'Netflix & Spotify Subs', 'amount': Decimal('649.00'), 'category': ent_cat, 'days_ago': 4, 'pm': 'DEBIT_CARD'},
        {'title': 'Pharmacy & Vitamins', 'amount': Decimal('520.00'), 'category': Category.objects.filter(name='Healthcare & Pharmacy').first(), 'days_ago': 3, 'pm': 'UPI'},
        {'title': 'Cafe Coffee Day & Snacks', 'amount': Decimal('380.00'), 'category': food_cat, 'days_ago': 2, 'pm': 'UPI'},
        {'title': 'Organic Vegetables & Milk', 'amount': Decimal('650.00'), 'category': groceries_cat, 'days_ago': 1, 'pm': 'CASH'},
        {'title': 'Python & Django Mastery Book', 'amount': Decimal('899.00'), 'category': Category.objects.filter(name='Education & Courses').first(), 'days_ago': 0, 'pm': 'UPI'},
    ]

    for exp in sample_expenses:
        Expense.objects.create(
            user=user,
            title=exp['title'],
            amount=exp['amount'],
            category=exp['category'],
            date=today - timedelta(days=exp['days_ago']),
            payment_method=exp['pm'],
            description=f"Transaction recorded on {today - timedelta(days=exp['days_ago'])}"
        )
