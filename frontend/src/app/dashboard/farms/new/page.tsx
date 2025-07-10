'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createFarm, getUser } from '@/lib/supabase'
import FarmLocationSelector from '@/components/Map/FarmLocationSelector'

interface FormData {
  name: string
  location_lat: number | null
  location_lng: number | null
  area_hectares: string
  crop_type: string
  planting_date: string
  harvest_date: string
}

interface FormErrors {
  name?: string
  location?: string
  area_hectares?: string
  crop_type?: string
  planting_date?: string
  harvest_date?: string
  general?: string
}

const COMMON_CROPS = [
  'Rice', 'Wheat', 'Corn (Maize)', 'Soybeans', 'Cotton', 'Sugarcane',
  'Potatoes', 'Tomatoes', 'Onions', 'Carrots', 'Lettuce', 'Cabbage',
  'Beans', 'Peas', 'Barley', 'Oats', 'Sunflower', 'Canola'
]

export default function NewFarmPage() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    name: '',
    location_lat: null,
    location_lng: null,
    area_hectares: '',
    crop_type: '',
    planting_date: '',
    harvest_date: ''
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const router = useRouter()

  useEffect(() => {
    async function loadUser() {
      try {
        const user = await getUser()
        if (!user) {
          router.push('/auth/login')
          return
        }
        setUser(user)
      } catch (err) {
        console.error('Error loading user:', err)
        router.push('/auth/login')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [router])

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'Farm name is required'
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Farm name must be at least 2 characters long'
    } else if (formData.name.trim().length > 100) {
      newErrors.name = 'Farm name must be less than 100 characters'
    }

    // Location validation
    if (!formData.location_lat || !formData.location_lng) {
      newErrors.location = 'Please select a location on the map'
    }

    // Area validation
    if (!formData.area_hectares.trim()) {
      newErrors.area_hectares = 'Farm area is required'
    } else {
      const area = parseFloat(formData.area_hectares)
      if (isNaN(area) || area <= 0) {
        newErrors.area_hectares = 'Please enter a valid area greater than 0'
      } else if (area > 100000) {
        newErrors.area_hectares = 'Farm area seems too large. Please verify the value.'
      }
    }

    // Crop type validation
    if (!formData.crop_type.trim()) {
      newErrors.crop_type = 'Crop type is required'
    } else if (formData.crop_type.trim().length < 2) {
      newErrors.crop_type = 'Crop type must be at least 2 characters long'
    }

    // Planting date validation
    if (!formData.planting_date) {
      newErrors.planting_date = 'Planting date is required'
    } else {
      const plantingDate = new Date(formData.planting_date)
      const today = new Date()
      const oneYearAgo = new Date()
      oneYearAgo.setFullYear(today.getFullYear() - 1)
      
      if (plantingDate > today) {
        newErrors.planting_date = 'Planting date cannot be in the future'
      } else if (plantingDate < oneYearAgo) {
        newErrors.planting_date = 'Planting date cannot be more than one year ago'
      }
    }

    // Harvest date validation
    if (!formData.harvest_date) {
      newErrors.harvest_date = 'Expected harvest date is required'
    } else {
      const harvestDate = new Date(formData.harvest_date)
      const plantingDate = new Date(formData.planting_date)
      const today = new Date()
      const oneYearFromNow = new Date()
      oneYearFromNow.setFullYear(today.getFullYear() + 1)

      if (formData.planting_date && harvestDate <= plantingDate) {
        newErrors.harvest_date = 'Harvest date must be after planting date'
      } else if (harvestDate > oneYearFromNow) {
        newErrors.harvest_date = 'Harvest date cannot be more than one year from now'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Clear error for this field when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const handleLocationSelect = (lat: number, lng: number) => {
    setFormData(prev => ({ ...prev, location_lat: lat, location_lng: lng }))
    
    // Clear location error when location is selected
    if (errors.location) {
      setErrors(prev => ({ ...prev, location: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setSubmitting(true)
    setErrors({})

    try {
      const farmData = {
        user_id: user.id,
        name: formData.name.trim(),
        location_lat: formData.location_lat!,
        location_lng: formData.location_lng!,
        area_hectares: parseFloat(formData.area_hectares),
        crop_type: formData.crop_type.trim(),
        planting_date: formData.planting_date,
        harvest_date: formData.harvest_date
      }

      await createFarm(farmData)
      router.push('/dashboard')
    } catch (error: any) {
      console.error('Error creating farm:', error)
      setErrors({ general: error.message || 'Failed to create farm. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 text-soil-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-soil-600 hover:text-soil-700">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="ml-3 text-2xl font-bold text-gray-900">Add New Farm</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                
                {/* General Error */}
                {errors.general && (
                  <div className="bg-red-50 border-l-4 border-red-400 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <p className="text-sm text-red-700">{errors.general}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Farm Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Farm Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                      errors.name 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : 'border-gray-300 focus:border-soil-500 focus:ring-soil-500'
                    }`}
                    placeholder="Enter a name for your farm"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                  )}
                </div>

                {/* Location Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Farm Location
                  </label>
                  <div className="border border-gray-300 rounded-md overflow-hidden">
                    <FarmLocationSelector
                      onLocationSelect={handleLocationSelect}
                      selectedLocation={
                        formData.location_lat && formData.location_lng 
                          ? { lat: formData.location_lat, lng: formData.location_lng }
                          : null
                      }
                    />
                  </div>
                  {errors.location && (
                    <p className="mt-1 text-sm text-red-600">{errors.location}</p>
                  )}
                  {formData.location_lat && formData.location_lng && (
                    <p className="mt-1 text-sm text-gray-500">
                      Selected coordinates: {formData.location_lat.toFixed(6)}, {formData.location_lng.toFixed(6)}
                    </p>
                  )}
                </div>

                {/* Farm Area */}
                <div>
                  <label htmlFor="area_hectares" className="block text-sm font-medium text-gray-700">
                    Farm Area (Hectares)
                  </label>
                  <input
                    type="number"
                    id="area_hectares"
                    name="area_hectares"
                    value={formData.area_hectares}
                    onChange={handleInputChange}
                    step="0.1"
                    min="0"
                    className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                      errors.area_hectares 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : 'border-gray-300 focus:border-soil-500 focus:ring-soil-500'
                    }`}
                    placeholder="Enter farm area in hectares"
                  />
                  {errors.area_hectares && (
                    <p className="mt-1 text-sm text-red-600">{errors.area_hectares}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    1 hectare = 2.47 acres = 10,000 square meters
                  </p>
                </div>

                {/* Crop Type */}
                <div>
                  <label htmlFor="crop_type" className="block text-sm font-medium text-gray-700">
                    Current Crop Type
                  </label>
                  <select
                    id="crop_type"
                    name="crop_type"
                    value={formData.crop_type}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                      errors.crop_type 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : 'border-gray-300 focus:border-soil-500 focus:ring-soil-500'
                    }`}
                  >
                    <option value="">Select a crop type</option>
                    {COMMON_CROPS.map(crop => (
                      <option key={crop} value={crop}>{crop}</option>
                    ))}
                    <option value="Other">Other (specify in notes)</option>
                  </select>
                  {errors.crop_type && (
                    <p className="mt-1 text-sm text-red-600">{errors.crop_type}</p>
                  )}
                </div>

                {/* Planting Date */}
                <div>
                  <label htmlFor="planting_date" className="block text-sm font-medium text-gray-700">
                    Planting Date
                  </label>
                  <input
                    type="date"
                    id="planting_date"
                    name="planting_date"
                    value={formData.planting_date}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                      errors.planting_date 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : 'border-gray-300 focus:border-soil-500 focus:ring-soil-500'
                    }`}
                  />
                  {errors.planting_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.planting_date}</p>
                  )}
                </div>

                {/* Harvest Date */}
                <div>
                  <label htmlFor="harvest_date" className="block text-sm font-medium text-gray-700">
                    Expected Harvest Date
                  </label>
                  <input
                    type="date"
                    id="harvest_date"
                    name="harvest_date"
                    value={formData.harvest_date}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                      errors.harvest_date 
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                        : 'border-gray-300 focus:border-soil-500 focus:ring-soil-500'
                    }`}
                  />
                  {errors.harvest_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.harvest_date}</p>
                  )}
                </div>

                {/* Submit buttons */}
                <div className="flex justify-end space-x-3 pt-6">
                  <Link
                    href="/dashboard"
                    className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500"
                  >
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="bg-soil-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-soil-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? 'Creating Farm...' : 'Create Farm'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 