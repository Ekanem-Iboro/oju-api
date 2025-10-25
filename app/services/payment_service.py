import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(amount: float, currency: str = "usd"):
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # convert to cents
            currency=currency
        )
        return intent
    except Exception as e:
        raise Exception(f"Error creating payment intent: {str(e)}")

def confirm_payment_intent(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent
    except Exception as e:
        raise Exception(f"Error confirming payment intent: {str(e)}")

def create_refund(payment_intent_id: str):
    try:
        refund = stripe.Refund.create(payment_intent=payment_intent_id)
        return refund
    except Exception as e:
        raise Exception(f"Error creating refund: {str(e)}")

def create_customer(email: str, source: str):
    try:
        customer = stripe.Customer.create(
            email=email,
            source=source
        )
        return customer
    except Exception as e:
        raise Exception(f"Error creating customer: {str(e)}")
