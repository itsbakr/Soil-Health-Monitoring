'use client'

import { useEffect, useState } from 'react'
import { Marker, Popup, useMapEvents } from 'react-leaflet'

interface LocationMarkerProps {
  selectedLocation?: { lat: number; lng: number } | null
  onLocationSelect: (lat: number, lng: number) => void
}

export default function LocationMarker({ selectedLocation, onLocationSelect }: LocationMarkerProps) {
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

  return position === null || position === undefined ? null : (
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

