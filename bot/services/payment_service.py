from __future__ import annotations

from typing import Optional, Tuple
from ..config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

try:
    from yookassa import Configuration, Payment
    from yookassa.domain.common.confirmation_type import ConfirmationType
except Exception:  # SDK may be missing in dev
    Configuration = None
    Payment = None
    ConfirmationType = None


class PaymentService:
    """Stub for payments integration. Extend for YooKassa or Telegram payments."""

    async def create_payment(self, order_id: int, amount: str, description: str, return_url: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Create payment. Returns (payment_id, confirmation_url or None).
        If YooKassa creds are set, creates a real redirect payment.
        Otherwise returns a test payment id.
        """
        if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY and Payment and Configuration and ConfirmationType:
            try:
                Configuration.configure(account_id=YOOKASSA_SHOP_ID, secret_key=YOOKASSA_SECRET_KEY)
                data = {
                    "amount": {"value": amount, "currency": "RUB"},
                    "capture": True,
                    "description": description,
                }
                if return_url:
                    data["confirmation"] = {"type": ConfirmationType.REDIRECT, "return_url": return_url}
                p = Payment.create(data)
                confirmation_url = None
                try:
                    confirmation_url = getattr(getattr(p, "confirmation", None), "confirmation_url", None)
                except Exception:
                    confirmation_url = None
                return p.id, confirmation_url
            except Exception:
                # On any API or auth error, fallback to test path
                pass
        # fallback test path
        return f"TEST-PAY-{order_id}", None

    async def check_payment(self, payment_id: str) -> Optional[str]:
        if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY and Payment and Configuration:
            Configuration.configure(account_id=YOOKASSA_SHOP_ID, secret_key=YOOKASSA_SECRET_KEY)
            try:
                p = Payment.find_one(payment_id)
                return getattr(p, "status", None)
            except Exception:
                return None
        # test path always paid
        return "paid"


