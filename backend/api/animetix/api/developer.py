import json
import secrets
import logging
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from animetix.models import Profile
from animetix.auth import DeveloperApiKeyAuthentication
from animetix.stripe_billing import StripeBillingService
from backend.adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from ..containers import get_container

logger = logging.getLogger("animetix.api.developer")


class DeveloperRAGView(APIView):
    """
    Developer B2B API endpoint to query the Animetix RAG engine.
    Requires authentication via X-API-Key header.
    """

    authentication_classes = [DeveloperApiKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get("query")
        media_type = request.data.get("media_type", "Anime")

        if not query:
            return Response({"error": "No query provided"}, status=400)

        user_id = str(request.user.id)
        try:
            # Get the RAG agent from container
            container = get_container()
            agent = container.agentic.agentic_rag()

            # Run the agentic RAG stream internally
            events = list(
                agent.plan_and_solve_stream(query, media_type, user_id=user_id)
            )

            # Find the final result event
            final_answer = ""
            for event in events:
                if event.get("type") == "result":
                    final_answer = event.get("content", "")
                    break

            # Fallback if no result event was explicitly emitted
            if not final_answer and events:
                for event in reversed(events):
                    if event.get("type") not in ("error", "status"):
                        final_answer = event.get("content", "")
                        break

            # 1. Log usage (Automatic Stripe reporting for Pro tier is handled inside log_usage)
            usage_adapter = DjangoUsageAdapter()
            usage_adapter.log_usage(
                engine="agentic_rag", units=1, user_id=request.user.id
            )

            return Response(
                {
                    "query": query,
                    "media_type": media_type,
                    "answer": final_answer,
                    "status": "success",
                }
            )

        except Exception as e:
            logger.exception("Error in DeveloperRAGView:")
            return Response({"error": str(e)}, status=500)


class DeveloperApiKeyView(APIView):
    """
    API endpoint for developers to view API key metadata and generate/regenerate keys.
    Requires session authentication (browser logged-in user).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        has_key = bool(profile.api_key_hash)

        return Response(
            {
                "tier": profile.tier,
                "has_api_key": has_key,
                "api_key_prefix": "ax_pro_" if has_key else None,
            }
        )

    def post(self, request):
        profile = request.user.profile

        if profile.tier != "pro":
            return Response(
                {"error": "API Key generation is restricted to Pro tier developers."},
                status=403,
            )

        # Generate a new raw key: ax_pro_<profile_id>_<secret>
        secret_token = secrets.token_hex(24)
        raw_key = f"ax_pro_{profile.id}_{secret_token}"

        # Save hashed key
        profile.set_api_key(raw_key)
        profile.save()

        # Return the raw key to the user (ONLY ONCE)
        return Response(
            {
                "api_key": raw_key,
                "warning": "Please copy this API key now. You will not be able to see it again!",
            },
            status=201,
        )


class CreateProSubscriptionCheckoutView(APIView):
    """
    Crée une session Stripe Checkout pour l'abonnement Pro API.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_id = getattr(
            settings, "STRIPE_PRO_API_PRICE_ID", "price_pro_api_standard"
        )

        success, result = StripeBillingService.create_subscription_checkout_session(
            user_id=request.user.id, price_id=price_id
        )

        if not success:
            return Response({"error": result}, status=500)

        return Response({"checkout_url": result})


class DeveloperSubscriptionMockView(APIView):
    """
    Mock endpoint to subscribe to the Pro tier (Local / Test Mode).
    Sets the user's tier to 'pro' and creates mock Stripe IDs.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile

        profile.tier = "pro"
        profile.stripe_customer_id = f"cus_mock_{secrets.token_hex(8)}"
        profile.stripe_subscription_id = f"sub_mock_{secrets.token_hex(8)}"
        profile.stripe_subscription_item_id = f"si_mock_{secrets.token_hex(8)}"
        profile.save()

        return Response(
            {
                "status": "subscribed",
                "tier": profile.tier,
                "stripe_customer_id": profile.stripe_customer_id,
            }
        )


class CreateBxCheckoutView(APIView):
    """
    Crée une session Stripe Checkout pour l'achat d'un pack de Bx.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")  # Nombre de Bx (ex: 10000)
        price = request.data.get("price_cents")  # Prix en centimes (ex: 499)

        if not amount or not price:
            return Response(
                {"error": "amount and price_cents are required"}, status=400
            )

        success, result = StripeBillingService.create_checkout_session(
            user_id=request.user.id, amount_bx=amount, price_cents=price
        )

        if not success:
            return Response({"error": result}, status=500)

        return Response({"checkout_url": result})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Stripe Webhook endpoint to handle checkout.session.completed
    and subscription lifecycle events.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

        # Parse payload
        try:
            event_data = json.loads(payload)
        except Exception:
            return HttpResponse(status=400)

        # Real Stripe Signature Verification
        if webhook_secret and sig_header:
            import stripe  # noqa: E402

            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except Exception as e:
                logger.error(f"Stripe Webhook signature verification failed: {e}")
                return HttpResponse(status=400)
        else:
            # Fallback for local testing / mock webhook delivery
            event = event_data

        event_type = event.get("type")
        logger.info(f"Stripe Webhook Event received: {event_type}")

        if event_type == "checkout.session.completed":
            session = event.get("data", {}).get("object", {})
            client_reference_id = session.get("client_reference_id")
            customer_id = session.get("customer")
            metadata = session.get("metadata", {})

            if client_reference_id:
                try:
                    profile = Profile.objects.get(user_id=client_reference_id)

                    # Cas 1 : Achat de pack de Bx
                    if metadata.get("transaction_type") == "bx_purchase":
                        amount = int(metadata.get("amount_bx", 0))
                        from ..models import WalletTransaction  # noqa: E402

                        profile.wallet_balance += amount
                        profile.save()

                        WalletTransaction.objects.create(
                            user=profile.user,
                            amount=amount,
                            transaction_type="purchase",
                            description=f"Achat via Stripe (Pack {amount} Bx)",
                        )
                        logger.info(
                            f"User {profile.user.username} bought {amount} Bx via Stripe."
                        )

                    # Cas 2 : Inscription Pro API
                    elif metadata.get("transaction_type") == "pro_subscription_upgrade":
                        subscription_id = session.get("subscription")
                        profile.tier = "pro"
                        profile.stripe_customer_id = customer_id
                        profile.stripe_subscription_id = subscription_id

                        if settings.STRIPE_SECRET_KEY and subscription_id:
                            import stripe  # noqa: E402

                            stripe.api_key = settings.STRIPE_SECRET_KEY
                            sub = stripe.Subscription.retrieve(subscription_id)
                            items = sub.get("items", {}).get("data", [])
                            if items:
                                profile.stripe_subscription_item_id = items[0].get("id")

                        profile.save()
                        logger.info(
                            f"User {profile.user.username} upgraded to Pro API via Stripe."
                        )
                except Profile.DoesNotExist:
                    logger.error(
                        f"Profile not found for user_id={client_reference_id} on checkout."
                    )

        elif event_type in (
            "customer.subscription.deleted",
            "customer.subscription.updated",
        ):
            subscription = event.get("data", {}).get("object", {})
            customer_id = subscription.get("customer")
            status = subscription.get("status")

            if (
                status in ("canceled", "unpaid")
                or event_type == "customer.subscription.deleted"
            ):
                try:
                    profile = Profile.objects.get(stripe_customer_id=customer_id)
                    profile.tier = "free"
                    profile.stripe_subscription_id = None
                    profile.stripe_subscription_item_id = None
                    # We preserve stripe_customer_id for future billing convenience
                    profile.save()
                    logger.info(
                        f"User {profile.user.username} subscription canceled/unpaid. Tier downgraded to free."
                    )
                except Profile.DoesNotExist:
                    logger.error(
                        f"Profile not found for customer_id={customer_id} on subscription cancel."
                    )

        return HttpResponse(status=200)
