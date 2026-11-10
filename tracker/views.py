import csv
import json
from decimal import Decimal
from datetime import datetime, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone

from .models import Expense, Income, Category, Budget, UserProfile
from .forms import (
    UserRegistrationForm, ExpenseForm, IncomeForm,
    BudgetForm, CategoryForm, UserProfileForm
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"Welcome {user.first_name or user.username}! Your account has been created successfully.")
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Current month's totals
    month_expenses = Expense.objects.filter(
        user=user, date__year=current_year, date__month=current_month
    )
    month_incomes = Income.objects.filter(
        user=user, date__year=current_year, date__month=current_month
    )

    total_expense_month = month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_income_month = month_incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_savings_month = total_income_month - total_expense_month

    # All-time totals
    all_expenses_total = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    all_incomes_total = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_worth = all_incomes_total - all_expenses_total

    # Savings rate
    savings_rate = 0
    if total_income_month > 0:
        savings_rate = round(float((net_savings_month / total_income_month) * 100), 1)

    # Category breakdown for Current Month (Expenses)
    category_data = month_expenses.values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')

    cat_labels = []
    cat_amounts = []
    cat_colors = []
    for item in category_data:
        cat_labels.append(item['category__name'] or 'Uncategorized')
        cat_amounts.append(float(item['total']))
        cat_colors.append(item['category__color'] or '#6b7280')

    # Monthly comparison (Last 6 months)
    monthly_labels = []
    monthly_income_data = []
    monthly_expense_data = []

    # Generate last 6 months list
    for i in range(5, -1, -1):
        target_month = current_month - i
        target_year = current_year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_name = date(target_year, target_month, 1).strftime('%b %Y')
        monthly_labels.append(month_name)

        exp_val = Expense.objects.filter(
            user=user, date__year=target_year, date__month=target_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        inc_val = Income.objects.filter(
            user=user, date__year=target_year, date__month=target_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        monthly_expense_data.append(float(exp_val))
        monthly_income_data.append(float(inc_val))

    # Budgets check for current month
    budgets = Budget.objects.filter(user=user, month=current_month, year=current_year).select_related('category')
    budget_alerts = []
    for b in budgets:
        spent = Expense.objects.filter(
            user=user, category=b.category, date__year=current_year, date__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        percent = round(float((spent / b.monthly_limit) * 100), 1) if b.monthly_limit > 0 else 0
        if percent >= 100:
            budget_alerts.append({
                'category': b.category.name,
                'limit': b.monthly_limit,
                'spent': spent,
                'percent': percent,
                'type': 'danger',
                'message': f"Over budget by ₹{spent - b.monthly_limit:.2f} ({percent}%)!"
            })
        elif percent >= 80:
            budget_alerts.append({
                'category': b.category.name,
                'limit': b.monthly_limit,
                'spent': spent,
                'percent': percent,
                'type': 'warning',
                'message': f"Approaching budget limit ({percent}% spent)."
            })

    # Recent transactions (combined 6 most recent expenses and incomes)
    recent_expenses = list(Expense.objects.filter(user=user).select_related('category')[:5])
    recent_incomes = list(Income.objects.filter(user=user).select_related('category')[:5])

    # Tag and combine
    combined = []
    for e in recent_expenses:
        combined.append({
            'id': e.id,
            'title': e.title,
            'amount': e.amount,
            'category': e.category,
            'date': e.date,
            'payment_method': e.get_payment_method_display(),
            'type': 'expense'
        })
    for inc in recent_incomes:
        combined.append({
            'id': inc.id,
            'title': inc.title,
            'amount': inc.amount,
            'category': inc.category,
            'date': inc.date,
            'payment_method': inc.get_payment_method_display(),
            'type': 'income'
        })
    combined.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = combined[:8]

    # Savings goal progress
    profile, _ = UserProfile.objects.get_or_create(user=user)
    savings_goal = profile.monthly_savings_goal
    savings_progress = round(float((net_savings_month / savings_goal) * 100), 1) if savings_goal > 0 and net_savings_month > 0 else 0
    if savings_progress > 100:
        savings_progress = 100

    context = {
        'total_expense_month': total_expense_month,
        'total_income_month': total_income_month,
        'net_savings_month': net_savings_month,
        'all_expenses_total': all_expenses_total,
        'all_incomes_total': all_incomes_total,
        'net_worth': net_worth,
        'savings_rate': savings_rate,
        'budget_alerts': budget_alerts,
        'recent_transactions': recent_transactions,
        'cat_labels': json.dumps(cat_labels),
        'cat_amounts': json.dumps(cat_amounts),
        'cat_colors': json.dumps(cat_colors),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_income_data': json.dumps(monthly_income_data),
        'monthly_expense_data': json.dumps(monthly_expense_data),
        'currency': profile.currency_symbol,
        'savings_goal': savings_goal,
        'savings_progress': savings_progress,
        'current_month_name': today.strftime('%B %Y'),
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
def expense_list_view(request):
    expenses = Expense.objects.filter(user=request.user).select_related('category')

    # Filtering
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    payment_method = request.GET.get('payment_method', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if query:
        expenses = expenses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    total_filtered = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    categories = Category.objects.filter(
        category_type='EXPENSE'
    ).filter(Q(user=request.user) | Q(user__isnull=True))

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'expenses': expenses,
        'total_filtered': total_filtered,
        'categories': categories,
        'payment_methods': Expense.PAYMENT_METHODS,
        'query': query,
        'selected_category': category_id,
        'selected_payment': payment_method,
        'start_date': start_date,
        'end_date': end_date,
        'currency': profile.currency_symbol,
    }
    return render(request, 'tracker/expense_list.html', context)


@login_required
def add_expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, f"Expense '{expense.title}' of ₹{expense.amount} added successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm(user=request.user, initial={'date': timezone.now().date()})

    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Add New Expense', 'btn_text': 'Add Expense'})


@login_required
def edit_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense '{expense.title}' updated successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense, user=request.user)

    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Edit Expense', 'btn_text': 'Update Expense'})


@login_required
def delete_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f"Expense '{title}' has been deleted.")
        return redirect('expense_list')
    return render(request, 'tracker/confirm_delete.html', {'item': expense, 'type': 'Expense'})


@login_required
def income_list_view(request):
    incomes = Income.objects.filter(user=request.user).select_related('category')

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    payment_method = request.GET.get('payment_method', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if query:
        incomes = incomes.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id:
        incomes = incomes.filter(category_id=category_id)
    if payment_method:
        incomes = incomes.filter(payment_method=payment_method)
    if start_date:
        incomes = incomes.filter(date__gte=start_date)
    if end_date:
        incomes = incomes.filter(date__lte=end_date)

    total_filtered = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    categories = Category.objects.filter(
        category_type='INCOME'
    ).filter(Q(user=request.user) | Q(user__isnull=True))

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'incomes': incomes,
        'total_filtered': total_filtered,
        'categories': categories,
        'payment_methods': Income.PAYMENT_METHODS,
        'query': query,
        'selected_category': category_id,
        'selected_payment': payment_method,
        'start_date': start_date,
        'end_date': end_date,
        'currency': profile.currency_symbol,
    }
    return render(request, 'tracker/income_list.html', context)


@login_required
def add_income_view(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST, user=request.user)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, f"Income '{income.title}' of ₹{income.amount} recorded successfully!")
            return redirect('income_list')
    else:
        form = IncomeForm(user=request.user, initial={'date': timezone.now().date()})

    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Add New Income', 'btn_text': 'Add Income'})


@login_required
def edit_income_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Income '{income.title}' updated successfully!")
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income, user=request.user)

    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Edit Income', 'btn_text': 'Update Income'})


@login_required
def delete_income_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        title = income.title
        income.delete()
        messages.success(request, f"Income '{title}' has been deleted.")
        return redirect('income_list')
    return render(request, 'tracker/confirm_delete.html', {'item': income, 'type': 'Income'})


@login_required
def budget_list_view(request):
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    budgets = Budget.objects.filter(user=request.user, month=month, year=year).select_related('category')

    budget_details = []
    total_budgeted = Decimal('0.00')
    total_spent_budgeted = Decimal('0.00')

    for b in budgets:
        spent = Expense.objects.filter(
            user=request.user, category=b.category, date__year=year, date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        percent = round(float((spent / b.monthly_limit) * 100), 1) if b.monthly_limit > 0 else 0
        remaining = b.monthly_limit - spent

        status = 'success'
        if percent >= 100:
            status = 'danger'
        elif percent >= 80:
            status = 'warning'

        budget_details.append({
            'budget': b,
            'spent': spent,
            'remaining': remaining,
            'percent': min(percent, 100),
            'actual_percent': percent,
            'status': status,
        })
        total_budgeted += b.monthly_limit
        total_spent_budgeted += spent

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'budget_details': budget_details,
        'selected_month': month,
        'selected_year': year,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'total_budgeted': total_budgeted,
        'total_spent_budgeted': total_spent_budgeted,
        'currency': profile.currency_symbol,
        'months_range': [(i, date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
    }
    return render(request, 'tracker/budget_list.html', context)


@login_required
def set_budget_view(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.cleaned_data['category']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            monthly_limit = form.cleaned_data['monthly_limit']

            budget, created = Budget.objects.update_or_create(
                user=request.user,
                category=category,
                month=month,
                year=year,
                defaults={'monthly_limit': monthly_limit}
            )
            action = "created" if created else "updated"
            messages.success(request, f"Budget for {category.name} has been {action} successfully!")
            return redirect('budget_list')
    else:
        today = timezone.now().date()
        form = BudgetForm(user=request.user, initial={'month': today.month, 'year': today.year})

    return render(request, 'tracker/budget_form.html', {'form': form})


@login_required
def delete_budget_view(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        cat_name = budget.category.name
        budget.delete()
        messages.success(request, f"Budget for '{cat_name}' has been deleted.")
        return redirect('budget_list')
    return render(request, 'tracker/confirm_delete.html', {'item': budget, 'type': 'Budget'})


@login_required
def analytics_reports_view(request):
    user = request.user
    today = timezone.now().date()
    current_year = today.year

    # Annual summary
    annual_expenses = Expense.objects.filter(user=user, date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    annual_income = Income.objects.filter(user=user, date__year=current_year).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    annual_savings = annual_income - annual_expenses

    # Monthly breakdown for whole current year
    monthly_stats = []
    for m in range(1, 13):
        m_name = date(current_year, m, 1).strftime('%B')
        exp = Expense.objects.filter(user=user, date__year=current_year, date__month=m).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        inc = Income.objects.filter(user=user, date__year=current_year, date__month=m).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        sav = inc - exp
        monthly_stats.append({
            'month': m_name,
            'income': inc,
            'expense': exp,
            'savings': sav,
        })

    # Payment method breakdown
    payment_breakdown = Expense.objects.filter(user=user).values('payment_method').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Category full breakdown
    all_cat_breakdown = Expense.objects.filter(user=user).values('category__name', 'category__color').annotate(
        total=Sum('amount'), count=Count('id')
    ).order_by('-total')

    profile, _ = UserProfile.objects.get_or_create(user=user)

    context = {
        'current_year': current_year,
        'annual_expenses': annual_expenses,
        'annual_income': annual_income,
        'annual_savings': annual_savings,
        'monthly_stats': monthly_stats,
        'payment_breakdown': payment_breakdown,
        'all_cat_breakdown': all_cat_breakdown,
        'currency': profile.currency_symbol,
    }
    return render(request, 'tracker/reports.html', context)


@login_required
def export_expenses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_{request.user.username}_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Category', 'Amount (INR)', 'Payment Method', 'Description'])

    expenses = Expense.objects.filter(user=request.user).select_related('category')
    for e in expenses:
        writer.writerow([
            e.date.strftime('%Y-%m-%d'),
            e.title,
            e.category.name if e.category else 'Uncategorized',
            e.amount,
            e.get_payment_method_display(),
            e.description or ''
        ])
    return response


@login_required
def export_incomes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="incomes_{request.user.username}_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Source / Title', 'Category', 'Amount (INR)', 'Payment Method', 'Description'])

    incomes = Income.objects.filter(user=request.user).select_related('category')
    for inc in incomes:
        writer.writerow([
            inc.date.strftime('%Y-%m-%d'),
            inc.title,
            inc.category.name if inc.category else 'Uncategorized',
            inc.amount,
            inc.get_payment_method_display(),
            inc.description or ''
        ])
    return response


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Update user model fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            messages.success(request, "Your profile and preferences have been updated.")
            return redirect('profile')
    else:
        form = UserProfileForm(
            instance=profile,
            initial={
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        )

    return render(request, 'tracker/profile.html', {'form': form})


@login_required
def seed_demo_data_view(request):
    """Seed sample realistic transactions and categories for immediate demonstration."""
    from .seed_data import populate_sample_data
    populate_sample_data(request.user)
    messages.success(request, "Sample realistic data loaded successfully! You can now explore charts, budgets, and transactions.")
    return redirect('dashboard')
