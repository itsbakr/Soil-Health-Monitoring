'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getUser, getFarms, signOut } from '@/lib/supabase'
import type { Database } from '@/lib/supabase'
import { HealthGauge } from '@/components/FarmerDashboard'

type Farm = Database['public']['Tables']['farms']['Row']

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [farms, setFarms] = useState<Farm[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const router = useRouter()

  useEffect(() => {
    async function loadUserAndFarms() {
      try {
        const user = await getUser()
        if (!user) {
          router.push('/auth/login')
          return
        }
        
        setUser(user)
        const farmsData = await getFarms(user.id)
        setFarms(farmsData || [])
      } catch (err) {
        setError('An unexpected error occurred')
      } finally {
        setLoading(false)
      }
    }

    loadUserAndFarms()
  }, [router])

  const handleLogout = async () => {
    try {
      await signOut()
      router.push('/')
      router.refresh()
    } catch (err) {
      console.error('Logout error:', err)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getDaysUntilHarvest = (harvestDate: string) => {
    const today = new Date()
    const harvest = new Date(harvestDate)
    const diffTime = harvest.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 0) return { text: 'Overdue', color: 'text-red-600', urgent: true }
    if (diffDays === 0) return { text: 'Today', color: 'text-amber-600', urgent: true }
    if (diffDays <= 7) return { text: `${diffDays}d`, color: 'text-amber-600', urgent: true }
    if (diffDays <= 30) return { text: `${diffDays}d`, color: 'text-blue-600', urgent: false }
    return { text: `${diffDays}d`, color: 'text-gray-600', urgent: false }
  }

  const totalArea = farms.reduce((sum, farm) => sum + Number(farm.area_hectares), 0)
  const uniqueCrops = new Set(farms.map(farm => farm.crop_type)).size

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-green-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <svg className="animate-spin h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="text-gray-600 font-medium">Loading your farm data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 via-white to-gray-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/20">
                <span className="text-xl">🌱</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">SoilGuard</h1>
                <p className="text-xs text-gray-500">Farm Health Monitor</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 hidden sm:block">
                {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
              </span>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-700 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Sign out"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.user_metadata?.full_name ? `, ${user.user_metadata.full_name.split(' ')[0]}` : ''}! 👋
          </h2>
          <p className="text-gray-600 mt-1">Here's how your farms are doing today.</p>
        </div>

        {farms.length > 0 ? (
          <>
            {/* Quick Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                    <span className="text-xl">🏡</span>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{farms.length}</p>
                    <p className="text-xs text-gray-500">Farm{farms.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                    <span className="text-xl">📐</span>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{totalArea.toFixed(1)}</p>
                    <p className="text-xs text-gray-500">Hectares</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                    <span className="text-xl">🌾</span>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{uniqueCrops}</p>
                    <p className="text-xs text-gray-500">Crop Type{uniqueCrops !== 1 ? 's' : ''}</p>
                  </div>
                </div>
              </div>
              
              <Link 
                href="/dashboard/farms/new"
                className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-sm p-4 text-white hover:shadow-lg hover:scale-[1.02] transition-all cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                    <span className="text-xl">➕</span>
                  </div>
                  <div>
                    <p className="font-semibold">Add Farm</p>
                    <p className="text-xs text-green-100">Quick setup</p>
                  </div>
                </div>
              </Link>
            </div>

            {/* Farm Cards */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Your Farms</h3>
                <span className="text-sm text-gray-500">{farms.length} total</span>
              </div>
              
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {farms.map((farm) => {
                  const harvest = getDaysUntilHarvest(farm.harvest_date)
                  
                  return (
                    <Link
                      key={farm.id}
                      href={`/dashboard/farms/${farm.id}`}
                      className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg hover:border-green-300 transition-all group"
                    >
                      {/* Farm Header */}
                      <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-4 text-white">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-bold text-lg group-hover:underline">{farm.name}</h4>
                            <p className="text-green-100 text-sm">{farm.area_hectares} hectares</p>
                          </div>
                          <span className="bg-white/20 px-2 py-1 rounded-lg text-xs font-medium">
                            {farm.crop_type}
                          </span>
                        </div>
                      </div>
                      
                      {/* Farm Body */}
                      <div className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <span className="text-sm text-gray-600">
                              {farm.location_lat.toFixed(4)}, {farm.location_lng.toFixed(4)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                          <div>
                            <p className="text-xs text-gray-500">Harvest in</p>
                            <p className={`font-semibold ${harvest.color}`}>{harvest.text}</p>
                          </div>
                          <div className="flex items-center gap-1 text-green-600 group-hover:gap-2 transition-all">
                            <span className="text-sm font-medium">View Details</span>
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>
            </div>
          </>
        ) : (
          /* Empty State */
          <div className="text-center py-16">
            <div className="max-w-md mx-auto">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
                <span className="text-4xl">🌱</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Welcome to SoilGuard!</h3>
              <p className="text-gray-600 mb-8">
                Start monitoring your farm's health with AI-powered satellite analysis. 
                Add your first farm to get started.
              </p>
              
              <Link
                href="/dashboard/farms/new"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-8 py-4 rounded-xl font-semibold shadow-lg shadow-green-500/25 hover:shadow-xl hover:scale-105 transition-all"
              >
                <span>🏡</span>
                Add Your First Farm
              </Link>
              
              <div className="mt-12 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-xl">📍</span>
                  </div>
                  <p className="text-sm text-gray-600">Drop a pin on the map</p>
                </div>
                <div>
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-xl">🛰️</span>
                  </div>
                  <p className="text-sm text-gray-600">We analyze satellite data</p>
                </div>
                <div>
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-xl">📊</span>
                  </div>
                  <p className="text-sm text-gray-600">Get zone-by-zone health</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}
      </main>
    </div>
  )
}
