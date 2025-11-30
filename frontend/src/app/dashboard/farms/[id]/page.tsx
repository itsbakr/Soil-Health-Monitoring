'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getFarm, getUser, deleteFarm } from '@/lib/supabase'
import type { Database } from '@/lib/supabase'
import { runCompleteAnalysis, analyzeSoilHealth, analyzeROI, pollAnalysisStatus, getSoilHealthReport, getROIReport, getZonalAnalysis, SoilHealthReport, ROIAnalysisReport, AnalysisHistorySoilHealth, AnalysisHistoryROI } from '@/lib/api'
import SoilHealthDisplay from '@/components/Analysis/SoilHealthDisplay'
import ROIDisplay from '@/components/Analysis/ROIDisplay'
import AnalysisHistory from '@/components/Analysis/AnalysisHistory'
import { InteractiveMapWrapper } from '@/components/Map/InteractiveMap'
import ZoneMap from '@/components/Analysis/ZoneMap'
import ZoneMapOverlay from '@/components/Analysis/ZoneMapOverlay'
import { HealthGauge, ActionList, ZoneAlertList } from '@/components/FarmerDashboard'

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
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState('')
  const [soilHealthReport, setSoilHealthReport] = useState<SoilHealthReport | null>(null)
  const [roiReport, setROIReport] = useState<ROIAnalysisReport | null>(null)
  const [showSoilHealth, setShowSoilHealth] = useState(false)
  const [showROI, setShowROI] = useState(false)
  const [zonalAnalysis, setZonalAnalysis] = useState<any>(null)
  const [zonalLoading, setZonalLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current')
  const router = useRouter()
  
  // Handler for selecting a historical analysis
  const handleSelectHistoricalAnalysis = (analysis: AnalysisHistorySoilHealth | AnalysisHistoryROI, type: 'soil' | 'roi') => {
    if (type === 'soil') {
      const soilAnalysis = analysis as AnalysisHistorySoilHealth
      setSoilHealthReport({
        id: soilAnalysis.id,
        farm_id: soilAnalysis.farm_id,
        status: 'completed',
        health_score: soilAnalysis.overall_health,
        overall_health: soilAnalysis.overall_health >= 75 ? 'Healthy' : soilAnalysis.overall_health >= 55 ? 'Moderate' : 'Needs Attention',
        summary: soilAnalysis.ai_summary || '',
        confidence_score: soilAnalysis.confidence_score,
        analysis_date: soilAnalysis.created_at,
        created_at: soilAnalysis.created_at,
        soil_indicators: {},
        vegetation_indices: {
          ndvi: soilAnalysis.ndvi,
          ndwi: soilAnalysis.ndwi
        },
        soil_condition_indices: { bsi: 0, si: 0, ci: 0, bi: 0 },
        deficiencies: [],
        recommendations: soilAnalysis.recommendations || [],
        zones: soilAnalysis.zone_data || [],
        problem_areas: soilAnalysis.problem_zones || [],
        satellite_source: soilAnalysis.satellite_source
      })
      setShowSoilHealth(true)
    } else {
      const roiAnalysis = analysis as AnalysisHistoryROI
      setROIReport({
        id: roiAnalysis.id,
        farm_id: roiAnalysis.farm_id,
        status: 'completed',
        analysis_date: roiAnalysis.created_at,
        current_crop: roiAnalysis.current_crop,
        crop_options: roiAnalysis.recommendations || [],
        economic_summary: roiAnalysis.ai_summary || '',
        reasoning: roiAnalysis.strategic_advice || '',
        risk_assessment: roiAnalysis.risk_assessment || {},
        market_forecast: roiAnalysis.market_data || {},
        cost_analysis: {
          estimated_input_costs: roiAnalysis.projected_costs || 0,
          estimated_revenue: roiAnalysis.projected_revenue || 0,
          net_profit_estimate: roiAnalysis.projected_profit || 0
        }
      })
      setShowROI(true)
    }
  }
  


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

  const handleAnalysis = async () => {
    if (!farm) return
    
    setAnalyzing(true)
    setAnalysisError('')
    setZonalLoading(true)
    
    try {
      console.log('🚀 Starting complete AI analysis for farm:', farm.name)
      
      // Run AI analysis and zonal analysis in parallel
      const [results, zonalData] = await Promise.all([
        runCompleteAnalysis(farm.id),
        getZonalAnalysis({ farm_id: farm.id, include_historical: false }).catch(err => {
          console.warn('Zonal analysis failed:', err)
          return null
        })
      ])
      
      setSoilHealthReport(results.soilHealth)
      setROIReport(results.roi)
      if (zonalData) {
        setZonalAnalysis(zonalData)
      }
      setShowSoilHealth(true) // Show soil health report first
      
      console.log('✅ Complete analysis finished - Soil Health, ROI, and Zonal data ready')
    } catch (err: any) {
      console.error('Analysis failed:', err)
      setAnalysisError(err.message || 'Analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
      setZonalLoading(false)
    }
  }

  const handleSoilHealthOnly = async () => {
    if (!farm) return
    
    setAnalyzing(true)
    setAnalysisError('')
    
    try {
      console.log('🔬 Starting soil health analysis for farm:', farm.name)
      
      const initialReport = await analyzeSoilHealth(farm.id)
      
      // Simple polling with type casting
      let attempts = 0
      let finalReport = initialReport
      
      while (attempts < 30 && finalReport.status !== 'completed') {
        if (finalReport.status === 'failed') {
          throw new Error('Analysis failed')
        }
        
        await new Promise(resolve => setTimeout(resolve, 2000))
        finalReport = await getSoilHealthReport(initialReport.id)
        attempts++
      }
      
      if (finalReport.status !== 'completed') {
        throw new Error('Analysis timeout - please try again')
      }
      
              setSoilHealthReport(finalReport)
      setShowSoilHealth(true)
    } catch (err: any) {
      console.error('Soil health analysis failed:', err)
      setAnalysisError(err.message || 'Soil health analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleROIOnly = async () => {
    if (!farm) return
    
    setAnalyzing(true)
    setAnalysisError('')
    
    try {
      const initialReport = await analyzeROI(farm.id)
      
      // Simple polling with type casting
      let attempts = 0
      let finalReport = initialReport
      
      while (attempts < 30 && finalReport.status !== 'completed') {
        if (finalReport.status === 'failed') {
          throw new Error('Analysis failed')
        }
        
        await new Promise(resolve => setTimeout(resolve, 2000))
        finalReport = await getROIReport(initialReport.id)
        attempts++
      }
      
      if (finalReport.status !== 'completed') {
        throw new Error('Analysis timeout - please try again')
      }
      
      setROIReport(finalReport)
      setShowROI(true)
    } catch (err: any) {
      console.error('ROI analysis failed:', err)
      setAnalysisError(err.message || 'ROI analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleZonalAnalysis = async () => {
    if (!farm) return
    
    setZonalLoading(true)
    setAnalysisError('')
    
    try {
      console.log('🗺️ Starting zonal analysis for farm:', farm.name)
      
      const data = await getZonalAnalysis({
        farm_id: farm.id,
        include_historical: false
      })
      
      setZonalAnalysis(data)
      console.log('✅ Zonal analysis complete:', data.zones?.length, 'zones analyzed')
    } catch (err: any) {
      console.error('Zonal analysis failed:', err)
      setAnalysisError(err.message || 'Zonal analysis failed. Please try again.')
    } finally {
      setZonalLoading(false)
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
                <div className="mt-5 space-x-2">
                  <button 
                    onClick={handleSoilHealthOnly}
                    disabled={analyzing}
                    className="bg-soil-600 hover:bg-soil-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:cursor-not-allowed"
                  >
                    {analyzing ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : 'Generate Report'}
                  </button>
                  {soilHealthReport && (
                    <button
                      onClick={() => setShowSoilHealth(true)}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                    >
                      View Report
                    </button>
                  )}
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
                <div className="mt-5 space-x-2">
                  <button 
                    onClick={handleROIOnly}
                    disabled={analyzing}
                    className="bg-crop-600 hover:bg-crop-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:cursor-not-allowed"
                  >
                    {analyzing ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : 'Analyze ROI'}
                  </button>
                  {roiReport && (
                    <button
                      onClick={() => setShowROI(true)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
                    >
                      View Report
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Complete Analysis Section */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6 mb-6">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">🚀 Complete AI Analysis</h3>
              <p className="text-gray-600 mb-4">
                Run comprehensive soil health and ROI analysis with our AI-powered agents
              </p>
              <button 
                onClick={handleAnalysis}
                disabled={analyzing}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-6 py-3 rounded-lg text-base font-medium transition-all disabled:cursor-not-allowed transform hover:scale-105"
              >
                {analyzing ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Running AI Analysis...
                  </>
                ) : '🧠 Start Complete AI Analysis'}
              </button>
              
              {analysisError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center">
                    <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm text-red-800">{analysisError}</span>
                  </div>
                </div>
              )}
              
              {(soilHealthReport || roiReport) && (
                <div className="mt-4 text-sm text-gray-600">
                  ✅ Analysis complete! Use the buttons above to view individual reports.
                </div>
              )}
            </div>
          </div>

          {/* Farm Health Map - Shown AFTER analysis is complete */}
          {(soilHealthReport || roiReport || zonalAnalysis) && (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
              <div className="px-4 py-5 sm:px-6 flex items-center justify-between">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center gap-2">
                    🗺️ Farm Health Map
                  </h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    Visual breakdown of health across different zones of your farm
                  </p>
                </div>
                {zonalAnalysis && (
                  <button
                    onClick={handleZonalAnalysis}
                    disabled={zonalLoading}
                    className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center gap-1"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh Map
                  </button>
                )}
              </div>
              
              <div className="border-t border-gray-200 p-6">
                {zonalAnalysis ? (
                  <div className="space-y-6">
                    {/* Satellite Map Overlay with Zone Health */}
                    <ZoneMapOverlay 
                      analysis={zonalAnalysis}
                      latitude={farm.location_lat}
                      longitude={farm.location_lng}
                      area={farm.area_hectares}
                      className="h-[500px] w-full"
                    />
                    
                    {/* Zone Alerts */}
                    {zonalAnalysis.zones && zonalAnalysis.zones.some((z: any) => z.health < 55) && (
                      <ZoneAlertList 
                        zones={zonalAnalysis.zones}
                        maxAlerts={3}
                      />
                    )}
                  </div>
                ) : zonalLoading ? (
                  <div className="text-center py-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                      <svg className="animate-spin h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">Generating Farm Health Map...</h4>
                    <p className="text-gray-500 text-sm">
                      Analyzing {farm.area_hectares} hectares with satellite imagery
                    </p>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <button
                      onClick={handleZonalAnalysis}
                      disabled={zonalLoading}
                      className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg text-sm font-medium transition-colors"
                    >
                      🛰️ Generate Farm Health Map
                    </button>
                    <p className="mt-2 text-xs text-gray-500">
                      See which zones of your farm need attention
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analysis History Section */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center gap-2">
                  📜 Analysis History
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  View previous soil health and ROI analyses for this farm
                </p>
              </div>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center gap-1"
              >
                {showHistory ? 'Hide History' : 'View History'}
                <svg className={`h-4 w-4 transition-transform ${showHistory ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            
            {showHistory && (
              <div className="border-t border-gray-200 p-6">
                <AnalysisHistory 
                  farmId={farm.id} 
                  onSelectAnalysis={handleSelectHistoricalAnalysis}
                />
              </div>
            )}
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
                <div className="space-y-4">
                  {/* Map Controls */}
                  <div className="flex flex-wrap items-center justify-between bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>
                        <strong>Coordinates:</strong> {farm.location_lat.toFixed(6)}, {farm.location_lng.toFixed(6)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                      <span>
                        <strong>Area:</strong> {farm.area_hectares} hectares
                      </span>
                    </div>
                  </div>

                  {/* Interactive Map */}
                  <InteractiveMapWrapper
                    latitude={farm.location_lat}
                    longitude={farm.location_lng}
                    farmName={farm.name}
                    area={farm.area_hectares}
                    cropType={farm.crop_type}
                    className="h-80 w-full rounded-lg shadow-lg border"
                  />

                  {/* Quick Actions */}
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={`https://www.google.com/maps?q=${farm.location_lat},${farm.location_lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Open in Google Maps
                    </a>
                    <a
                      href={`https://earth.google.com/web/@${farm.location_lat},${farm.location_lng},1000a,2000d/data=CgIgAQ`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      View in Google Earth
                    </a>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(`${farm.location_lat}, ${farm.location_lng}`)
                        // You could add a toast notification here
                      }}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-soil-500"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v6a2 2 0 002 2h2m0 0h2m0 0h2a2 2 0 002-2V7a2 2 0 00-2-2h-2m0 0V3a2 2 0 012-2h2a2 2 0 012 2v2M8 5a2 2 0 012-2h2a2 2 0 012 2v2m0 0v6a2 2 0 01-2 2h-2a2 2 0 01-2-2V7m0 0V5a2 2 0 012-2h2a2 2 0 012 2v2" />
                      </svg>
                      Copy Coordinates
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Analysis Results Modals */}
      {showSoilHealth && soilHealthReport && (
        <SoilHealthDisplay 
          report={soilHealthReport} 
          onClose={() => setShowSoilHealth(false)}
        />
      )}

      {showROI && roiReport && (
        <ROIDisplay 
          report={roiReport} 
          onClose={() => setShowROI(false)}
        />
      )}
    </div>
  )
} 