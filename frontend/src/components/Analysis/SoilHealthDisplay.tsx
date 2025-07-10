'use client'

import { SoilHealthReport } from '@/lib/api'
import { useState } from 'react'

interface SoilHealthDisplayProps {
  report: SoilHealthReport
  onClose?: () => void
}

export default function SoilHealthDisplay({ report, onClose }: SoilHealthDisplayProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'recommendations'>('overview')

  // Helper functions
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100'
    if (score >= 60) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getHealthIcon = (score: number) => {
    if (score >= 80) return '🌱'
    if (score >= 60) return '⚠️'
    return '🚨'
  }

  const getIndicatorStatus = (value: number, optimal: { min: number; max: number }) => {
    if (value >= optimal.min && value <= optimal.max) return 'optimal'
    if (value < optimal.min * 0.8 || value > optimal.max * 1.2) return 'critical'
    return 'suboptimal'
  }

  const getIndicatorColor = (status: string) => {
    switch (status) {
      case 'optimal': return 'text-green-600 bg-green-50 border-green-200'
      case 'suboptimal': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // Optimal ranges for soil indicators
  const optimalRanges = {
    ph_level: { min: 6.0, max: 7.5 },
    moisture_content: { min: 0.3, max: 0.7 },
    temperature: { min: 18, max: 28 },
    salinity: { min: 0, max: 0.2 },
    organic_matter: { min: 2.0, max: 5.0 }
  }

  const vegetationOptimal = {
    ndvi: { min: 0.6, max: 1.0 },
    ndwi: { min: 0.0, max: 0.3 },
    savi: { min: 0.5, max: 0.8 },
    evi: { min: 0.3, max: 0.7 },
    ndmi: { min: 0.3, max: 0.7 }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-soil-600 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">🔬 Soil Health Analysis Report</h2>
              <p className="text-soil-100 text-sm">
                Generated {new Date(report.analysis_date).toLocaleDateString()} • 
                Confidence: {(report.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col h-full max-h-[calc(90vh-80px)]">
          
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'details', label: 'Detailed Analysis', icon: '🔍' },
                { id: 'recommendations', label: 'Recommendations', icon: '💡' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-soil-500 text-soil-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-6">
            
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                
                {/* Overall Health Score */}
                <div className="text-center">
                  <div className={`inline-flex items-center px-6 py-3 rounded-full text-2xl font-bold ${getHealthColor(report.confidence_score * 100)}`}>
                    <span className="mr-2 text-3xl">{getHealthIcon(report.confidence_score * 100)}</span>
                    {(report.confidence_score * 100).toFixed(0)}/100
                  </div>
                  <h3 className="mt-2 text-xl font-semibold text-gray-900 capitalize">
                    {report.overall_health} Soil Health
                  </h3>
                  <p className="text-gray-600 max-w-2xl mx-auto">
                    {report.summary}
                  </p>
                </div>

                {/* Key Indicators Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  
                  {/* Soil Indicators */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">🌱 Soil Chemistry</h4>
                    <div className="space-y-2">
                      {Object.entries(report.soil_indicators).map(([key, value]) => {
                        const optimal = optimalRanges[key as keyof typeof optimalRanges]
                        const status = optimal ? getIndicatorStatus(value, optimal) : 'unknown'
                        return (
                          <div key={key} className={`p-2 rounded border ${getIndicatorColor(status)}`}>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium capitalize">
                                {key.replace('_', ' ')}
                              </span>
                              <span className="text-sm font-bold">
                                {value.toFixed(2)}{key === 'ph_level' ? '' : key === 'temperature' ? '°C' : '%'}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Vegetation Indices */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">🌿 Vegetation Health</h4>
                    <div className="space-y-2">
                      {Object.entries(report.vegetation_indices).map(([key, value]) => {
                        const optimal = vegetationOptimal[key as keyof typeof vegetationOptimal]
                        const status = optimal ? getIndicatorStatus(value, optimal) : 'unknown'
                        return (
                          <div key={key} className={`p-2 rounded border ${getIndicatorColor(status)}`}>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium uppercase">
                                {key}
                              </span>
                              <span className="text-sm font-bold">
                                {value.toFixed(3)}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">⚡ Quick Actions</h4>
                    <div className="space-y-2">
                      {report.deficiencies.length > 0 && (
                        <div className="p-2 rounded bg-red-50 border border-red-200">
                          <div className="text-sm font-medium text-red-800">
                            🚨 {report.deficiencies.length} Issue{report.deficiencies.length > 1 ? 's' : ''} Found
                          </div>
                          <div className="text-xs text-red-600 mt-1">
                            Check recommendations for solutions
                          </div>
                        </div>
                      )}
                      
                      <div className="p-2 rounded bg-blue-50 border border-blue-200">
                        <div className="text-sm font-medium text-blue-800">
                          📈 {report.recommendations.length} Recommendation{report.recommendations.length > 1 ? 's' : ''}
                        </div>
                        <div className="text-xs text-blue-600 mt-1">
                          AI-powered improvement suggestions
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                
                {/* Soil Condition Indices */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">🔬 Detailed Soil Analysis</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(report.soil_condition_indices).map(([key, value]) => (
                      <div key={key} className="bg-white border rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-soil-600">
                          {value.toFixed(3)}
                        </div>
                        <div className="text-sm font-medium text-gray-900 uppercase">
                          {key}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {key === 'bsi' && 'Bare Soil Index'}
                          {key === 'si' && 'Salinity Index'}
                          {key === 'ci' && 'Coloration Index'}
                          {key === 'bi' && 'Brightness Index'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Deficiencies */}
                {report.deficiencies.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-red-800 mb-4">⚠️ Identified Issues</h3>
                    <div className="space-y-3">
                      {report.deficiencies.map((deficiency, index) => (
                        <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="ml-3">
                              <p className="text-sm text-red-800">{deficiency}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">💡 AI-Powered Recommendations</h3>
                
                {report.recommendations.length > 0 ? (
                  <div className="space-y-4">
                    {report.recommendations.map((recommendation, index) => (
                      <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <div className="bg-green-500 rounded-full p-1">
                              <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-green-800">
                              Recommendation #{index + 1}
                            </div>
                            <p className="text-sm text-green-700 mt-1">
                              {recommendation}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="mt-2">Your soil health looks great! No specific recommendations at this time.</p>
                  </div>
                )}

                {/* Analysis Metadata */}
                <div className="bg-gray-50 rounded-lg p-4 mt-8">
                  <h4 className="font-semibold text-gray-900 mb-2">📋 Analysis Details</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Analysis ID:</span>
                      <span className="ml-2 font-mono text-gray-900">{report.id}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <span className="ml-2 capitalize font-medium text-green-600">{report.status}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Generated:</span>
                      <span className="ml-2 text-gray-900">
                        {new Date(report.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">AI Confidence:</span>
                      <span className="ml-2 font-semibold text-gray-900">
                        {(report.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 