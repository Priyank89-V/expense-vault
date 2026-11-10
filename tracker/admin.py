from django.contrib import admin
from .models import Category, Expense, Income, Budget, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'color', 'user', 'is_default')
    list_filter = ('category_type', 'is_default')
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'amount', 'date', 'payment_method')
    list_filter = ('category', 'payment_method', 'date')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'date'


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'amount', 'date', 'payment_method')
    list_filter = ('category', 'payment_method', 'date')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'monthly_limit', 'month', 'year')
    list_filter = ('month', 'year', 'category')
    search_fields = ('user__username', 'category__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency_symbol', 'monthly_savings_goal', 'phone_number')
    search_fields = ('user__username', 'user__email')
