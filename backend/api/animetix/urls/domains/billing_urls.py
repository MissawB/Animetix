from django.urls import path

from ... import api_views
from ...api import billing
from ...views.billing import billing_alert_webhook

urlpatterns = [
    path(
        "billing/wallet/mine/", billing.WalletMineView.as_view(), name="api_wallet_mine"
    ),
    path(
        "billing/wallet/watch-ad/",
        billing.WalletWatchAdView.as_view(),
        name="api_wallet_watch_ad",
    ),
    path(
        "billing/wallet/balance/",
        billing.WalletBalanceView.as_view(),
        name="api_wallet_balance",
    ),
    path("billing/webhook/", billing_alert_webhook, name="api_billing_webhook"),
    path(
        "billing/log_ad_event/",
        api_views.AdEventLoggingAPIView.as_view(),
        name="api_log_ad_event",
    ),
    path(
        "admin/financials/",
        api_views.AdminFinancialsAPIView.as_view(),
        name="api_admin_financials",
    ),
    path(
        "admin/economics/",
        api_views.AdminEconomicAuditAPIView.as_view(),
        name="api_admin_economics",
    ),
]
