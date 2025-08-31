'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'

// Dynamically import map components to avoid SSR issues
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { 
  ssr: false,
  loading: () => <div className="w-full h-64 bg-gray-100 animate-pulse rounded-lg flex items-center justify-center">
    <span className="text-gray-500">Loading map...</span>
  </div>
})
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false })
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false })

interface InteractiveMapProps {
  latitude: number
  longitude: number
  farmName?: string
  area?: number
  cropType?: string
  className?: string
}

export default function InteractiveMap({ 
  latitude, 
  longitude, 
  farmName = "Farm Location",
  area,
  cropType,
  className = "h-64 w-full rounded-lg" 
}: InteractiveMapProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return (
      <div className={`${className} bg-gray-100 animate-pulse flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-soil-600 mx-auto mb-2"></div>
          <span className="text-gray-500 text-sm">Loading interactive map...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      <MapContainer
        center={[latitude, longitude]}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <Marker position={[latitude, longitude]}>
          <Popup>
            <div className="text-center p-2">
              <h3 className="font-semibold text-gray-900 mb-2">{farmName}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p><strong>Coordinates:</strong> {latitude.toFixed(6)}, {longitude.toFixed(6)}</p>
                {area && <p><strong>Area:</strong> {area} hectares</p>}
                {cropType && <p><strong>Crop:</strong> {cropType}</p>}
              </div>
              <div className="mt-3 flex space-x-2 text-xs">
                <a 
                  href={`https://www.google.com/maps?q=${latitude},${longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 transition-colors"
                >
                  📍 Google Maps
                </a>
                <a 
                  href={`https://earth.google.com/web/@${latitude},${longitude},1000a,2000d/data=CgIgAQ`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600 transition-colors"
                >
                  🌍 Google Earth
                </a>
              </div>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}

// Create a wrapper component that handles loading state
export function InteractiveMapWrapper(props: InteractiveMapProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className={`${props.className} bg-gradient-to-r from-blue-50 to-green-50 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center`}>
        <div className="text-center p-6">
          <div className="animate-pulse">
            <div className="h-12 w-12 bg-gray-300 rounded-full mx-auto mb-4"></div>
            <div className="h-4 bg-gray-300 rounded w-32 mx-auto mb-2"></div>
            <div className="h-3 bg-gray-300 rounded w-24 mx-auto"></div>
          </div>
        </div>
      </div>
    )
  }

  return <InteractiveMap {...props} />
}
