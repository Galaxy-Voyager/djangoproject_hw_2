from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet
from .views_stripe import (
    StripeCheckoutView,
    StripePaymentStatusView,
    StripeWebhookView,
    PaymentSuccessView,
    PaymentCancelView
)


app_name = "payments"


router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")


urlpatterns = [
    path("", include(router.urls)),
    path("stripe/checkout/", StripeCheckoutView.as_view(), name="stripe-checkout"),
    path("stripe/status/<str:session_id>/", StripePaymentStatusView.as_view(), name="stripe-status"),
    path("stripe/status/", StripePaymentStatusView.as_view(), name="stripe-status-no-id"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
]
