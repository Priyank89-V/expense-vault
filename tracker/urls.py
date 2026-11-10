from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Auth
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Expenses CRUD
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/add/', views.add_expense_view, name='add_expense'),
    path('expenses/<int:pk>/edit/', views.edit_expense_view, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense_view, name='delete_expense'),

    # Income CRUD
    path('incomes/', views.income_list_view, name='income_list'),
    path('incomes/add/', views.add_income_view, name='add_income'),
    path('incomes/<int:pk>/edit/', views.edit_income_view, name='edit_income'),
    path('incomes/<int:pk>/delete/', views.delete_income_view, name='delete_income'),

    # Budgets
    path('budgets/', views.budget_list_view, name='budget_list'),
    path('budgets/set/', views.set_budget_view, name='set_budget'),
    path('budgets/<int:pk>/delete/', views.delete_budget_view, name='delete_budget'),

    # Analytics & Reports
    path('reports/', views.analytics_reports_view, name='reports'),

    # Data Exports
    path('export/expenses/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('export/incomes/csv/', views.export_incomes_csv, name='export_incomes_csv'),

    # User Profile & Demo Data
    path('profile/', views.profile_view, name='profile'),
    path('seed-demo-data/', views.seed_demo_data_view, name='seed_demo_data'),
]
