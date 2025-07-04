# Stripe Connect Integration for TradeHub

## Key Concepts

### Stripe Connect Overview
- **Purpose**: Enable marketplace payments with escrow-style functionality
- **Flow**: Collect payments from customers → Hold in platform account → Transfer to service providers
- **Benefits**: Platform control, delayed payouts, fee collection, fraud protection

### Implementation Strategy

#### 1. Connected Accounts
- Service providers must create Stripe Connect accounts
- Use Express accounts for simplified onboarding
- Platform manages the onboarding flow

#### 2. Payment Flow
1. **Customer Payment**: Customer pays platform for service
2. **Escrow Hold**: Funds held in platform's Stripe account
3. **Service Completion**: Customer confirms work completion
4. **Transfer**: Funds transferred to service provider minus platform fee

#### 3. Key Components Needed

**Models:**
- `StripeAccount` - Store provider's connected account info
- `Payment` - Track payment transactions
- `Transfer` - Track transfers to providers
- `Dispute` - Handle payment disputes

**API Endpoints:**
- `/api/payments/create-payment-intent` - Create payment for job
- `/api/payments/confirm-payment` - Confirm payment completion
- `/api/payments/transfer-funds` - Transfer to provider
- `/api/stripe/onboard-provider` - Provider onboarding
- `/api/stripe/account-status` - Check account status

#### 4. Security & Compliance
- Use Stripe's secure payment processing
- Implement webhook verification
- Store minimal payment data
- Follow PCI compliance guidelines

## Available Stripe Keys
- Public Key: Available via VITE_STRIPE_PUBLIC_KEY environment variable
- Secret Key: Available via STRIPE_SECRET_KEY environment variable

