'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getFarm, getUser, deleteFarm } from '@/lib/supabase'
import type { Database } from '@/lib/supabase'

type Farm = Database['public']['Tables']['farms']['Row']

interface FarmDetailPageProps {
  params: { id: string }
}

export default function FarmDetailPage({ params }: FarmDetailPageProps) {
  const [user, setUser] = useState<any>(null)
  const [farm, setFarm] = useState<Farm | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  useEffect(() => {
    async function loadFarmAndUser() {
      try {
        // Get current user
        const user = await getUser()
        if (!user) {
          router.push('/auth/login')
          return
        }
        
        setUser(user)

        // Get farm details
        const farmData = await getFarm(params.id, user.id)
        if (!farmData) {
          setError('Farm not found or you do not have access to it')
          return
        }
        
        setFarm(farmData)
      } catch (err: any) {
        console.error('Error loading farm:', err)
        setError(err.message || 'Failed to load farm details')
      } finally {
        setLoading(false)
      }
    }

    loadFarmAndUser()
  }, [params.id, router])

  const handleDelete = async () => {
    if (!farm || !user) return
    
    const confirmed = window.confirm(
      `Are you sure you want to delete "${farm.name}"? This action cannot be undone.`
    )
    
    if (!confirmed) return

    setDeleting(true)
    try {
      await deleteFarm(farm.id, user.id)
      router.push('/dashboard')
    } catch (err: any) {
      console.error('Error deleting farm:', err)
      setError(err.message || 'Failed to delete farm')
      setDeleting(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getDaysUntilHarvest = (harvestDate: string) => {
    const today = new Date()
    const harvest = new Date(harvestDate)
    const diffTime = harvest.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`
    } else if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return '1 day'
    } else {
      return `${diffDays} days`
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
          <p className="mt-2 text-gray-600">Loading farm details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 text-red-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Error</h3>
          <p className="mt-1 text-sm text-gray-500">{error}</p>
          <div className="mt-6">
            <Link
              href="/dashboard"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-soil-600 hover:bg-soil-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!farm) {
    return null
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
              <div className="ml-3">
                <h1 className="text-2xl font-bold text-gray-900">{farm.name}</h1>
                <p className="text-sm text-gray-500">Farm Details</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete Farm'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          
          {/* Farm Overview */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Farm Overview</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Basic information about your farm
              </p>
            </div>
            <div className="border-t border-gray-200">
              <dl>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Farm Name</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{farm.name}</dd>
                </div>
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Location</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    {farm.location_lat.toFixed(6)}, {farm.location_lng.toFixed(6)}
                  </dd>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Area</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    {farm.area_hectares} hectares ({(farm.area_hectares * 2.47).toFixed(1)} acres)
                  </dd>
                </div>
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Current Crop</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {farm.crop_type}
                    </span>
                  </dd>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Planting Date</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    {formatDate(farm.planting_date)}
                  </dd>
                </div>
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Expected Harvest</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    {formatDate(farm.harvest_date)}
                    <span className="ml-2 text-xs text-gray-500">
                      ({getDaysUntilHarvest(farm.harvest_date)})
                    </span>
                  </dd>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Created</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    {formatDate(farm.created_at)}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Action Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            
            {/* Soil Health Analysis */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-soil-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <div className="text-lg font-medium text-gray-900">Soil Health Analysis</div>
                    <div className="mt-1 text-sm text-gray-500">
                      Get detailed soil health assessment using satellite data and AI analysis
                    </div>
                  </div>
                </div>
                <div className="mt-5">
                  <button className="bg-soil-600 hover:bg-soil-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                    Generate Report
                  </button>
                  <span className="ml-2 text-xs text-gray-500">(Coming Soon)</span>
                </div>
              </div>
            </div>

            {/* Crop Recommendations */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-crop-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <div className="text-lg font-medium text-gray-900">ROI Analysis</div>
                    <div className="mt-1 text-sm text-gray-500">
                      Get crop recommendations and ROI projections based on soil conditions
                    </div>
                  </div>
                </div>
                <div className="mt-5">
                  <button className="bg-crop-600 hover:bg-crop-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                    Analyze ROI
                  </button>
                  <span className="ml-2 text-xs text-gray-500">(Coming Soon)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Location Map Placeholder */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Farm Location</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Geographic location and boundaries of your farm
              </p>
            </div>
            <div className="border-t border-gray-200">
              <div className="p-6">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Interactive Map</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Coordinates: {farm.location_lat.toFixed(6)}, {farm.location_lng.toFixed(6)}
                  </p>
                  <p className="mt-1 text-xs text-gray-400">
                    Interactive map visualization will be available in future updates
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 