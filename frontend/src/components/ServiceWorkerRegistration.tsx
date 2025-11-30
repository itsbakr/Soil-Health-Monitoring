'use client'

import { useEffect } from 'react'

export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      return
    }

    const registerServiceWorker = async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        })

        console.log('[PWA] Service worker registered:', registration.scope)

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New content available
                console.log('[PWA] New content available')
                
                // You could show a toast notification here
                if (window.confirm('New version available! Reload to update?')) {
                  window.location.reload()
                }
              }
            })
          }
        })

        // Handle messages from service worker
        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data?.type === 'SYNC_COMPLETE') {
            console.log('[PWA] Sync complete:', event.data.count, 'items synced')
          }
        })

      } catch (error) {
        console.error('[PWA] Service worker registration failed:', error)
      }
    }

    // Register when window loads
    window.addEventListener('load', registerServiceWorker)

    return () => {
      window.removeEventListener('load', registerServiceWorker)
    }
  }, [])

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      console.log('[PWA] Back online')
      // Could trigger sync here
    }

    const handleOffline = () => {
      console.log('[PWA] Gone offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return null
}

