"use client";

import { useState } from 'react';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import { Book } from '@/services/book-service';
import { useToast } from '@/components/providers/ToastProvider';

interface PaymentFormProps {
    books: Book[];
    totalAmount: number;
    onSuccess: (paymentIntent: any) => void;
    onError: (error: string) => void;
}

const cardElementOptions = {
    style: {
        base: {
            fontSize: '16px',
            color: '#424770',
            '::placeholder': {
                color: '#aab7c4',
            },
        },
        invalid: {
            color: '#9e2146',
        },
    },
};

export default function PaymentForm({ books, totalAmount, onSuccess, onError }: PaymentFormProps) {
    const stripe = useStripe();
    const elements = useElements();
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [name, setName] = useState('');
    const { showToast } = useToast();

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!stripe || !elements) {
            showToast('Stripe has not loaded yet. Please try again.', 'error');
            return;
        }

        setLoading(true);

        try {
            // Create payment intent on the server
            const response = await fetch('/api/payment/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: totalAmount * 100, // Convert to cents
                    currency: 'usd',
                    books: books.map(book => ({ id: book.id, title: book.title })),
                    customerEmail: email,
                    customerName: name,
                }),
            });

            const { clientSecret, error } = await response.json();

            if (error) {
                showToast(error, 'error');
                onError(error);
                return;
            }

            // Confirm payment with Stripe
            const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
                payment_method: {
                    card: elements.getElement(CardElement)!,
                    billing_details: {
                        name: name,
                        email: email,
                    },
                },
            });

            if (stripeError) {
                showToast(stripeError.message || 'Payment failed', 'error');
                onError(stripeError.message || 'Payment failed');
            } else if (paymentIntent.status === 'succeeded') {
                showToast('Payment successful! Your order has been placed.', 'success');
                onSuccess(paymentIntent);
            }
        } catch (error) {
            console.error('Payment error:', error);
            showToast('An error occurred during payment. Please try again.', 'error');
            onError('Payment failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Payment Details</h2>

            {/* Order Summary */}
            <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Summary</h3>
                <div className="space-y-2">
                    {books.map((book) => (
                        <div key={book.id} className="flex justify-between text-sm">
                            <span className="text-gray-600">{book.title}</span>
                            <span className="font-medium">${book.price}</span>
                        </div>
                    ))}
                    <div className="border-t pt-2">
                        <div className="flex justify-between font-semibold">
                            <span>Total</span>
                            <span>${totalAmount.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                {/* Customer Information */}
                <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                        Full Name
                    </label>
                    <input
                        type="text"
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                        placeholder="John Doe"
                    />
                </div>

                <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email Address
                    </label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                        placeholder="john@example.com"
                    />
                </div>

                {/* Card Details */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Card Details
                    </label>
                    <div className="border border-gray-300 rounded-md p-3">
                        <CardElement options={cardElementOptions} />
                    </div>
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={!stripe || loading}
                    className="w-full bg-amber-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {loading ? (
                        <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Processing...
                        </div>
                    ) : (
                        `Pay $${totalAmount.toFixed(2)}`
                    )}
                </button>
            </form>

            {/* Security Notice */}
            <div className="mt-4 text-xs text-gray-500 text-center">
                <p>🔒 Your payment information is secure and encrypted</p>
                <p>Powered by Stripe</p>
            </div>
        </div>
    );
} 