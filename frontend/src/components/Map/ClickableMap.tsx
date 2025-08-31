'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'

// Dynamically import map components to avoid SSR issues
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { 
  ssr: false,
  loading: () => <div className="w-full h-64 bg-gray-100 animate-pulse rounded-lg flex items-center justify-center">
    <span className="text-gray-500">Loading interactive map...</span>
  </div>
})
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false })
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false })
const useMapEvents = dynamic(() => import('react-leaflet').then(mod => mod.useMapEvents), { ssr: false })

interface ClickableMapProps {
  selectedLocation?: { lat: number; lng: number } | null
  onLocationSelect: (lat: number, lng: number) => void
  className?: string
}

function LocationMarker({ selectedLocation, onLocationSelect }: { 
  selectedLocation?: { lat: number; lng: number } | null
  onLocationSelect: (lat: number, lng: number) => void 
}) {
  const [position, setPosition] = useState(selectedLocation)

  const map = useMapEvents({
    click: (e) => {
      const newPos = { lat: e.latlng.lat, lng: e.latlng.lng }
      setPosition(newPos)
      onLocationSelect(e.latlng.lat, e.latlng.lng)
      map.flyTo(e.latlng, map.getZoom())
    },
  })

  useEffect(() => {
    setPosition(selectedLocation)
  }, [selectedLocation])

  return position === null ? null : (
    <Marker position={[position.lat, position.lng]}>
      <Popup>
        <div className="text-center">
          <h3 className="font-semibold text-gray-900 mb-2">Selected Location</h3>
          <p className="text-sm text-gray-600">
            <strong>Coordinates:</strong><br />
            {position.lat.toFixed(6)}, {position.lng.toFixed(6)}
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Click anywhere on the map to change location
          </p>
        </div>
      </Popup>
    </Marker>
  )
}

export default function ClickableMap({ 
  selectedLocation, 
  onLocationSelect,
  className = "h-64 w-full rounded-lg" 
}: ClickableMapProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return (
      <div className={`${className} bg-gray-100 animate-pulse flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-soil-600 mx-auto mb-2"></div>
          <span className="text-gray-500 text-sm">Loading clickable map...</span>
        </div>
      </div>
    )
  }

  // Default to a central location if no location is selected
  const center = selectedLocation ? [selectedLocation.lat, selectedLocation.lng] : [39.8283, -98.5795] // Center of USA

  return (
    <div className={className}>
      <MapContainer
        center={center as [number, number]}
        zoom={selectedLocation ? 15 : 4}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <LocationMarker selectedLocation={selectedLocation} onLocationSelect={onLocationSelect} />
      </MapContainer>
      
      {/* Instructions overlay */}
      <div className="absolute bottom-2 left-2 bg-white bg-opacity-90 backdrop-blur-sm px-3 py-2 rounded-lg shadow-lg text-xs text-gray-700 max-w-xs z-10">
        <div className="flex items-center space-x-1">
          <svg className="h-4 w-4 text-soil-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
          </svg>
          <span>Click anywhere on the map to select farm location</span>
        </div>
      </div>
    </div>
  )
}

// Create a wrapper component that handles loading state
export function ClickableMapWrapper(props: ClickableMapProps) {
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

  return <ClickableMap {...props} />
}
