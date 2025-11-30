import type { Metadata, Viewport } from 'next'
import { Inter, Space_Grotesk } from 'next/font/google'
import './globals.css'
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
})

const spaceGrotesk = Space_Grotesk({ 
  subsets: ['latin'],
  variable: '--font-space'
})

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#16a34a',
}

export const metadata: Metadata = {
  title: 'SoilGuard - Farm Health Monitor',
  description: 'AI-powered soil health monitoring for farmers. Get zone-by-zone analysis using satellite data to detect land degradation and improve crop yields.',
  keywords: 'soil health, agriculture, farming, satellite data, land degradation, crop recommendations, precision agriculture',
  authors: [{ name: 'SoilGuard Team' }],
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'SoilGuard',
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: 'website',
    siteName: 'SoilGuard',
    title: 'SoilGuard - Farm Health Monitor',
    description: 'AI-powered soil health monitoring for farmers. Detect land degradation early with satellite analysis.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SoilGuard - Farm Health Monitor',
    description: 'AI-powered soil health monitoring for farmers.',
  },
  icons: {
    icon: [
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
    ],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`h-full ${inter.variable} ${spaceGrotesk.variable}`}>
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body className={`${inter.className} h-full bg-gray-50 text-gray-900 antialiased`}>
        <div id="root" className="min-h-full">
          {children}
        </div>
        <ServiceWorkerRegistration />
      </body>
    </html>
  )
} 
