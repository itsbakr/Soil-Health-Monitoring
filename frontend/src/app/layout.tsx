import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export const metadata: Metadata = {
  title: 'Soil Health Monitor - Agricultural ROI Platform',
  description: 'Comprehensive soil health monitoring and agricultural ROI optimization platform using satellite data analysis and AI-powered insights.',
  keywords: 'soil health, agriculture, farming, satellite data, ROI, crop recommendations',
  authors: [{ name: 'Soil Health Team' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 text-gray-900`}>
        <div id="root" className="min-h-full">
          {children}
        </div>
      </body>
    </html>
  )
} 