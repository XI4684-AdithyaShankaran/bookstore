"use client";

import Header from '@/components/layout/Header';
import BookCard from '@/components/books/BookCard';
import { useGetCartQuery, useUpdateCartItemMutation, useRemoveFromCartMutation } from '@/store/api/cartApi';
import type { CartItem } from '@/store/api/cartApi';

export default function CartPage() {
  const { data: cartItems, isLoading, error } = useGetCartQuery();
  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeFromCart] = useRemoveFromCartMutation();

  const calculateTotal = () => {
    if (!cartItems) return 0;
    return cartItems.reduce((total: number, item: CartItem) => {
      return total + (item.book.price || 0) * item.quantity;
    }, 0);
  };

  const handleQuantityChange = async (id: number, newQuantity: number) => {
    try {
      await updateCartItem({ id, quantity: newQuantity });
    } catch (error) {
      console.error('Failed to update cart item:', error);
    }
  };

  const handleRemoveItem = async (id: number) => {
    try {
      await removeFromCart(id);
    } catch (error) {
      console.error('Failed to remove item:', error);
    }
  };

  return (
    <div className="min-h-screen bg-amber-50">
      <Header />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Shopping Cart
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Review your selected books and complete your purchase.
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
            <span className="ml-2 text-gray-600">Loading cart...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-500">Failed to load cart. Please try again.</p>
          </div>
        ) : cartItems && cartItems.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Cart Items</h2>
                <div className="space-y-4">
                  {cartItems.map((item: CartItem) => (
                    <div key={item.id} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                      <div className="flex-1">
                        <BookCard book={{
                            id: item.book.id,
                            title: item.book.title,
                            author: item.book.author,
                            price: item.book.price,
                            rating: 0,
                            pages: 0,
                            year: 0,
                            language: '',
                            isbn: '',
                            isbn13: '',
                            ratings_count: 0,
                            text_reviews_count: 0,
                            image_url: item.book.image_url
                        }} />
                      </div>
                      <div className="flex items-center space-x-2">
                        <button 
                          className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                          onClick={() => handleQuantityChange(item.id, Math.max(1, item.quantity - 1))}
                        >
                          -
                        </button>
                        <span className="w-12 text-center">{item.quantity}</span>
                        <button 
                          className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                          onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                        >
                          +
                        </button>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">
                          ${((item.book.price || 0) * item.quantity).toFixed(2)}
                        </p>
                        <button 
                          className="text-red-600 hover:text-red-700 text-sm"
                          onClick={() => handleRemoveItem(item.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm p-6 sticky top-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Order Summary</h2>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subtotal</span>
                    <span className="font-semibold">${calculateTotal().toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Shipping</span>
                    <span className="font-semibold">$5.99</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tax</span>
                    <span className="font-semibold">${(calculateTotal() * 0.08).toFixed(2)}</span>
                  </div>
                  <hr className="border-gray-200" />
                  <div className="flex justify-between">
                    <span className="text-lg font-semibold text-gray-900">Total</span>
                    <span className="text-lg font-semibold text-gray-900">
                      ${(calculateTotal() + 5.99 + (calculateTotal() * 0.08)).toFixed(2)}
                    </span>
                  </div>
                </div>
                <button className="w-full bg-amber-600 text-white py-3 rounded-lg font-semibold hover:bg-amber-700 transition-colors mt-6">
                  Proceed to Checkout
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-sm p-8 max-w-md mx-auto">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="8" cy="21" r="1"></circle>
                  <circle cx="19" cy="21" r="1"></circle>
                  <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"></path>
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Your Cart is Empty</h3>
              <p className="text-gray-600 mb-4">
                Start shopping to add books to your cart.
              </p>
              <button className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors">
                Browse Books
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 