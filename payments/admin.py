from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "payment_date",
        "course",
        "lesson",
        "amount",
        "payment_method",
    )
    list_filter = ("payment_method", "payment_date", "course")
    search_fields = ("user__email", "course__title", "lesson__title")
    readonly_fields = ("payment_date",)

    fieldsets = (
        ("Основная информация", {"fields": ("user", "payment_date")}),
        ("Оплата", {"fields": ("course", "lesson", "amount", "payment_method")}),
    )
