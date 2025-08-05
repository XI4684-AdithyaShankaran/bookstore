'use client'

import { Provider } from 'react-redux'
import { store } from '@/store'
import { ToastProvider } from '@/components/providers/ToastProvider'
import { SessionProvider } from 'next-auth/react'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <Provider store={store}>
        <ToastProvider>
          <main className="min-h-screen bg-gray-50">
            {children}
          </main>
        </ToastProvider>
      </Provider>
    </SessionProvider>
  )
} 