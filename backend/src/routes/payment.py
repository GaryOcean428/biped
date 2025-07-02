from flask import Blueprint, request, jsonify, current_app
import stripe
import json
import os
from datetime import datetime, timedelta
from ..models.user import db, User
from ..models.job import Job
from ..models.payment import Payment, Transfer, StripeAccount, Dispute

payment_bp = Blueprint('payment', __name__)

# Configure Stripe with environment variable
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@payment_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'payment'})

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create a payment intent for a job"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        customer_id = data.get('customer_id')
        
        if not job_id or not customer_id:
            return jsonify({'error': 'Job ID and customer ID are required'}), 400
        
        # Get job details
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Get customer
        customer = User.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Calculate amounts
        total_amount = int(job.budget * 100)  # Convert to cents
        platform_fee = int(total_amount * 0.05)  # 5% platform fee
        provider_amount = total_amount - platform_fee
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='usd',
            metadata={
                'job_id': job_id,
                'customer_id': customer_id,
                'provider_id': job.user_id,
                'platform_fee': platform_fee,
                'provider_amount': provider_amount
            },
            description=f'Payment for job: {job.title}'
        )
        
        # Create payment record
        payment = Payment(
            job_id=job_id,
            customer_id=customer_id,
            provider_id=job.user_id,
            stripe_payment_intent_id=intent.id,
            total_amount=total_amount,
            platform_fee=platform_fee,
            provider_amount=provider_amount,
            status='pending',
            description=f'Payment for job: {job.title}',
            auto_release_date=datetime.utcnow() + timedelta(days=7)  # Auto-release after 7 days
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment_id': payment.id,
            'total_amount': total_amount,
            'platform_fee': platform_fee,
            'provider_amount': provider_amount
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    """Confirm payment completion and update status"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID is required'}), 400
        
        # Get payment record
        payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            payment.status = 'paid'
            payment.paid_at = datetime.utcnow()
            payment.stripe_charge_id = intent.charges.data[0].id if intent.charges.data else None
            payment.payment_method = intent.charges.data[0].payment_method_details.type if intent.charges.data else None
            
            db.session.commit()
            
            return jsonify({
                'message': 'Payment confirmed successfully',
                'payment': payment.to_dict()
            })
        else:
            return jsonify({'error': f'Payment not successful. Status: {intent.status}'}), 400
            
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/release-escrow', methods=['POST'])
def release_escrow():
    """Release escrowed funds to service provider"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        customer_id = data.get('customer_id')
        
        if not payment_id or not customer_id:
            return jsonify({'error': 'Payment ID and customer ID are required'}), 400
        
        # Get payment
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Verify customer owns this payment
        if payment.customer_id != customer_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if payment is paid and not already released
        if payment.status != 'paid':
            return jsonify({'error': 'Payment must be in paid status'}), 400
        
        if payment.escrow_released:
            return jsonify({'error': 'Escrow already released'}), 400
        
        # Get provider's Stripe account
        provider_stripe_account = StripeAccount.query.filter_by(user_id=payment.provider_id).first()
        if not provider_stripe_account or not provider_stripe_account.payouts_enabled:
            return jsonify({'error': 'Provider Stripe account not ready for payouts'}), 400
        
        # Create transfer to provider
        transfer = stripe.Transfer.create(
            amount=payment.provider_amount,
            currency='usd',
            destination=provider_stripe_account.stripe_account_id,
            metadata={
                'payment_id': payment_id,
                'job_id': payment.job_id,
                'provider_id': payment.provider_id
            }
        )
        
        # Create transfer record
        transfer_record = Transfer(
            payment_id=payment_id,
            provider_id=payment.provider_id,
            stripe_account_id=provider_stripe_account.stripe_account_id,
            stripe_transfer_id=transfer.id,
            amount=payment.provider_amount,
            status='paid',
            description=f'Transfer for job payment {payment_id}'
        )
        
        # Update payment status
        payment.status = 'transferred'
        payment.escrow_released = True
        payment.escrow_release_date = datetime.utcnow()
        payment.transferred_at = datetime.utcnow()
        
        db.session.add(transfer_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Escrow released successfully',
            'transfer': transfer_record.to_dict()
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/onboard-provider', methods=['POST'])
def onboard_provider():
    """Create Stripe Connect account for service provider"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user already has Stripe account
        existing_account = StripeAccount.query.filter_by(user_id=user_id).first()
        if existing_account:
            return jsonify({'error': 'User already has a Stripe account'}), 400
        
        # Create Stripe Connect account
        account = stripe.Account.create(
            type='express',
            country='US',
            email=user.email,
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
            business_type='individual',
            metadata={
                'user_id': user_id,
                'platform': 'tradehub'
            }
        )
        
        # Create account record
        stripe_account = StripeAccount(
            user_id=user_id,
            stripe_account_id=account.id,
            account_type='express',
            charges_enabled=account.charges_enabled,
            payouts_enabled=account.payouts_enabled,
            details_submitted=account.details_submitted
        )
        
        db.session.add(stripe_account)
        db.session.commit()
        
        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{request.host_url}stripe/reauth",
            return_url=f"{request.host_url}stripe/return",
            type='account_onboarding',
        )
        
        return jsonify({
            'account_id': account.id,
            'onboarding_url': account_link.url,
            'stripe_account': stripe_account.to_dict()
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/account-status/<int:user_id>', methods=['GET'])
def get_account_status(user_id):
    """Get Stripe account status for a user"""
    try:
        # Get user's Stripe account
        stripe_account = StripeAccount.query.filter_by(user_id=user_id).first()
        if not stripe_account:
            return jsonify({'error': 'No Stripe account found'}), 404
        
        # Get account details from Stripe
        account = stripe.Account.retrieve(stripe_account.stripe_account_id)
        
        # Update local record
        stripe_account.charges_enabled = account.charges_enabled
        stripe_account.payouts_enabled = account.payouts_enabled
        stripe_account.details_submitted = account.details_submitted
        stripe_account.requirements_due = json.dumps(account.requirements.currently_due) if account.requirements else None
        stripe_account.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'account_status': {
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'details_submitted': account.details_submitted,
                'requirements_due': account.requirements.currently_due if account.requirements else [],
                'disabled_reason': account.requirements.disabled_reason if account.requirements else None
            },
            'stripe_account': stripe_account.to_dict()
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/payments/<int:user_id>', methods=['GET'])
def get_user_payments(user_id):
    """Get payments for a user (as customer or provider)"""
    try:
        # Get payments where user is customer or provider
        customer_payments = Payment.query.filter_by(customer_id=user_id).all()
        provider_payments = Payment.query.filter_by(provider_id=user_id).all()
        
        return jsonify({
            'customer_payments': [p.to_dict() for p in customer_payments],
            'provider_payments': [p.to_dict() for p in provider_payments]
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not endpoint_secret:
            return jsonify({'error': 'Webhook secret not configured'}), 400
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Update payment status
            payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent['id']).first()
            if payment:
                payment.status = 'paid'
                payment.paid_at = datetime.utcnow()
                db.session.commit()
        
        elif event['type'] == 'transfer.paid':
            transfer = event['data']['object']
            # Update transfer status
            transfer_record = Transfer.query.filter_by(stripe_transfer_id=transfer['id']).first()
            if transfer_record:
                transfer_record.status = 'paid'
                transfer_record.transferred_at = datetime.utcnow()
                db.session.commit()
        
        elif event['type'] == 'charge.dispute.created':
            dispute = event['data']['object']
            # Create dispute record
            payment = Payment.query.filter_by(stripe_charge_id=dispute['charge']).first()
            if payment:
                dispute_record = Dispute(
                    payment_id=payment.id,
                    stripe_dispute_id=dispute['id'],
                    amount=dispute['amount'],
                    currency=dispute['currency'],
                    reason=dispute['reason'],
                    status=dispute['status'],
                    evidence_due_by=datetime.fromtimestamp(dispute['evidence_details']['due_by']) if dispute.get('evidence_details') else None
                )
                db.session.add(dispute_record)
                db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

