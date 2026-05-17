from typing import List, Optional
from datetime import datetime
from django.db.models import Sum
from core.ports.donation_port import DonationPort
from core.domain.entities.donation import Donation as DomainDonation
from animetix.models import Donation as DjangoDonation

class DjangoDonationAdapter(DonationPort):
    def save(self, donation: DomainDonation) -> DomainDonation:
        print(f"DEBUG: Saving donation for transaction {donation.transaction_id}")
        django_donation = DjangoDonation.objects.create(
            user_id=donation.user_id,
            amount=donation.amount,
            currency=donation.currency,
            platform=donation.platform,
            transaction_id=donation.transaction_id,
            message=donation.message
        )
        print(f"DEBUG: Saved django donation with id {django_donation.id}")
        donation.id = django_donation.id
        donation.created_at = django_donation.created_at
        return donation

    def get_user_donations(self, user_id: int) -> List[DomainDonation]:
        django_donations = DjangoDonation.objects.filter(user_id=user_id).order_by('-created_at')
        return [self._to_domain(d) for d in django_donations]

    def get_total_donations(self, since: Optional[datetime] = None) -> float:
        query = DjangoDonation.objects.all()
        if since:
            query = query.filter(created_at__gte=since)
        return query.aggregate(total=Sum('amount'))['total'] or 0.0

    def get_recent_donations(self, limit: int = 10) -> List[DomainDonation]:
        django_donations = DjangoDonation.objects.all().order_by('-created_at')[:limit]
        return [self._to_domain(d) for d in django_donations]

    def _to_domain(self, django_donation: DjangoDonation) -> DomainDonation:
        return DomainDonation(
            id=django_donation.id,
            user_id=django_donation.user_id,
            amount=django_donation.amount,
            currency=django_donation.currency,
            platform=django_donation.platform,
            transaction_id=django_donation.transaction_id,
            message=django_donation.message,
            created_at=django_donation.created_at
        )
