import time
import uuid
import logging
from django.conf import settings

logger = logging.getLogger("animetix.stripe_billing")


class StripeBillingService:
    @staticmethod
    def create_checkout_session(user_id, amount_bx, price_cents, currency="eur"):
        """
        Creates a Stripe Checkout Session for a Bx pack.
        """
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe_key:
            return None, "mock_checkout_url"

        import stripe
        stripe.api_key = stripe_key

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'Pack {amount_bx} Berrix (Bx) - Animetix',
                            'description': 'Crédits pour l\'utilisation des fonctionnalités IA d\'Animetix.',
                        },
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                client_reference_id=user_id,
                metadata={
                    'transaction_type': 'bx_purchase',
                    'amount_bx': amount_bx
                },
                success_url=f"{settings.FRONTEND_URL}/pricing?status=success",
                cancel_url=f"{settings.FRONTEND_URL}/pricing?status=cancel",
            )
            return True, session.url
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return False, str(e)

    @staticmethod
    def report_usage(profile, quantity=1):
        """
        Reports metered usage to Stripe.
        If STRIPE_SECRET_KEY is not set (mock/local mode), logs the event locally.
        """
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        
        # Local mock mode
        if not stripe_key:
            logger.info(
                f"[MOCK STRIPE] Reported usage of {quantity} units for "
                f"profile ID={profile.id} (Customer: {profile.stripe_customer_id or 'none'})"
            )
            return True, "mock_success"

        import stripe
        stripe.api_key = stripe_key
        
        use_meters = getattr(settings, 'STRIPE_USE_METERS', True)
        
        try:
            if use_meters:
                # Use modern Stripe Billing Meters API
                if not profile.stripe_customer_id:
                    logger.warning(f"No stripe_customer_id for profile ID={profile.id}. Cannot report usage.")
                    return False, "missing_customer_id"
                
                event_name = getattr(settings, 'STRIPE_METER_EVENT_NAME', 'rag_api_requests')
                event = stripe.billing.MeterEvent.create(
                    event_name=event_name,
                    payload={
                        "value": str(quantity),
                        "stripe_customer_id": profile.stripe_customer_id,
                    },
                    identifier=f"evt_{profile.id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                )
                logger.info(f"Successfully reported meter event to Stripe: {event.id}")
                return True, event.id
            else:
                # Fallback to subscription item usage record (classic)
                if not profile.stripe_subscription_item_id:
                    logger.warning(f"No stripe_subscription_item_id for profile ID={profile.id}. Cannot report usage.")
                    return False, "missing_subscription_item_id"
                
                record = stripe.SubscriptionItem.create_usage_record(
                    profile.stripe_subscription_item_id,
                    quantity=quantity,
                    timestamp=int(time.time()),
                    action="increment"
                )
                logger.info(f"Successfully created Stripe Usage Record: {record.id}")
                return True, record.id
                
        except Exception as e:
            logger.error(f"Failed to report usage to Stripe: {e}")
            return False, str(e)
