'use client'

import { useState, useEffect, useRef } from 'react'

interface FarmLocationSelectorProps {
  onLocationSelect: (lat: number, lng: number) => void
  selectedLocation?: { lat: number; lng: number } | null
}

export default function FarmLocationSelector({ onLocationSelect, selectedLocation }: FarmLocationSelectorProps) {
  const [manualCoords, setManualCoords] = useState({
    latitude: selectedLocation?.lat?.toString() || '',
    longitude: selectedLocation?.lng?.toString() || ''
  })
  const [useCurrentLocation, setUseCurrentLocation] = useState(false)
  const [locationError, setLocationError] = useState('')
  const [gettingLocation, setGettingLocation] = useState(false)

  useEffect(() => {
    if (selectedLocation) {
      setManualCoords({
        latitude: selectedLocation.lat.toString(),
        longitude: selectedLocation.lng.toString()
      })
    }
  }, [selectedLocation])

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by this browser')
      return
    }

    setGettingLocation(true)
    setLocationError('')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude
        const lng = position.coords.longitude
        
        setManualCoords({
          latitude: lat.toString(),
          longitude: lng.toString()
        })
        
        onLocationSelect(lat, lng)
        setGettingLocation(false)
        setUseCurrentLocation(true)
      },
      (error) => {
        let errorMessage = 'Unable to get your location'
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location access denied by user'
            break
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable'
            break
          case error.TIMEOUT:
            errorMessage = 'Location request timed out'
            break
        }
        setLocationError(errorMessage)
        setGettingLocation(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    )
  }

  const handleManualCoordChange = (field: 'latitude' | 'longitude', value: string) => {
    setManualCoords(prev => ({ ...prev, [field]: value }))
    setUseCurrentLocation(false)
    
    // Validate and update parent if both coordinates are valid
    const lat = field === 'latitude' ? parseFloat(value) : parseFloat(manualCoords.latitude)
    const lng = field === 'longitude' ? parseFloat(value) : parseFloat(manualCoords.longitude)
    
    if (!isNaN(lat) && !isNaN(lng) && isValidCoordinate(lat, lng)) {
      onLocationSelect(lat, lng)
      setLocationError('')
    }
  }

  const isValidCoordinate = (lat: number, lng: number): boolean => {
    return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
  }

  const validateCurrentCoords = (): boolean => {
    const lat = parseFloat(manualCoords.latitude)
    const lng = parseFloat(manualCoords.longitude)
    
    if (isNaN(lat) || isNaN(lng)) {
      setLocationError('Please enter valid numeric coordinates')
      return false
    }
    
    if (!isValidCoordinate(lat, lng)) {
      setLocationError('Latitude must be between -90 and 90, Longitude must be between -180 and 180')
      return false
    }
    
    setLocationError('')
    return true
  }

  const getLocationName = (lat: number, lng: number): string => {
    // Simple coordinate display - in a real app, you'd use reverse geocoding
    return `${lat.toFixed(6)}, ${lng.toFixed(6)}`
  }

  return (
    <div className="space-y-4 p-4 bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Select Farm Location</h3>
        <div className="flex items-center space-x-2">
                     <svg className="h-5 w-5 text-soil-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-sm text-gray-700">Pin your farm location</span>
        </div>
      </div>

      {/* Current Location Button */}
      <div className="flex justify-center">
        <button
          type="button"
          onClick={getCurrentLocation}
          disabled={gettingLocation}
                     className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-soil-600 hover:bg-soil-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {gettingLocation ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Getting Location...
            </>
          ) : (
            <>
              <svg className="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Use Current Location
            </>
          )}
        </button>
      </div>

      {/* Manual Coordinate Entry */}
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Or enter coordinates manually:</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="latitude" className="block text-xs font-medium text-gray-700 mb-1">
              Latitude
            </label>
            <input
              type="number"
              id="latitude"
              step="any"
              value={manualCoords.latitude}
              onChange={(e) => handleManualCoordChange('latitude', e.target.value)}
              placeholder="e.g., 40.7128"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-soil-500 focus:ring-soil-500 sm:text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">-90 to 90</p>
          </div>
          <div>
            <label htmlFor="longitude" className="block text-xs font-medium text-gray-700 mb-1">
              Longitude
            </label>
            <input
              type="number"
              id="longitude"
              step="any"
              value={manualCoords.longitude}
              onChange={(e) => handleManualCoordChange('longitude', e.target.value)}
              placeholder="e.g., -74.0060"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-soil-500 focus:ring-soil-500 sm:text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">-180 to 180</p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {locationError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-700">{locationError}</p>
          </div>
        </div>
      )}

      {/* Selected Location Display */}
      {selectedLocation && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-green-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <div>
              <p className="text-sm font-medium text-green-700">Location Selected</p>
              <p className="text-xs text-green-600">
                {getLocationName(selectedLocation.lat, selectedLocation.lng)}
                {useCurrentLocation && ' (Current Location)'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Map Placeholder */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-white">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">Interactive Map</h3>
        <p className="mt-1 text-sm text-gray-500">
          {selectedLocation 
            ? `Farm location pinned at ${getLocationName(selectedLocation.lat, selectedLocation.lng)}`
            : 'Use the location button above or enter coordinates manually'
          }
        </p>
        {selectedLocation && (
                       <div className="mt-4 p-3 bg-soil-50 rounded-md">
               <p className="text-xs text-soil-700">
              📍 Farm coordinates: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lng.toFixed(6)}
            </p>
          </div>
        )}
      </div>

      {/* Helpful Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
        <div className="flex">
          <svg className="h-5 w-5 text-blue-400 mr-2 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Tips for accurate location:</p>
            <ul className="text-xs space-y-1">
              <li>• Use "Current Location" if you're at the farm site</li>
              <li>• For manual entry, use GPS coordinates from your mapping app</li>
              <li>• Coordinates should point to the center of your farm area</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
} 