'use client'

import { SoilHealthReport } from '@/lib/api'
import { useState, ReactNode } from 'react'

interface SoilHealthDisplayProps {
  report: SoilHealthReport
  onClose?: () => void
}

// Enhanced markdown formatter that produces clean, well-spaced output
const formatMarkdownText = (text: string | undefined): ReactNode => {
  if (!text) return null;
  
  // Split into lines first for better structure
  const lines = text.split('\n').filter(line => line.trim());
  
  return (
    <div className="space-y-2">
      {lines.map((line, lineIndex) => {
        const trimmedLine = line.trim();
        
        // Check if line is a header (bold text ending with colon or all caps)
        const isHeader = /^\*\*[^*]+\*\*:?$/.test(trimmedLine) || 
                        (trimmedLine === trimmedLine.toUpperCase() && trimmedLine.length > 3);
        
        // Remove markdown bold markers
        const cleanLine = trimmedLine.replace(/\*\*([^*]+)\*\*/g, '$1');
        
        // Header styling
        if (isHeader || cleanLine.endsWith(':')) {
          return (
            <div key={lineIndex} className="mt-3 first:mt-0">
              <strong className="text-gray-900 font-semibold block">{cleanLine}</strong>
            </div>
          );
        }
        
        // Bullet point or numbered list
        if (cleanLine.startsWith('•') || cleanLine.startsWith('-') || /^\d+\./.test(cleanLine)) {
          const bulletContent = cleanLine.replace(/^[•\-]\s*/, '').replace(/^\d+\.\s*/, '');
          return (
            <div key={lineIndex} className="flex items-start ml-4">
              <span className="text-gray-400 mr-2">•</span>
              <span>{bulletContent}</span>
            </div>
          );
        }
        
        // Key-value pairs (contains colon but not at end)
        if (cleanLine.includes(':') && !cleanLine.endsWith(':')) {
          const [key, ...valueParts] = cleanLine.split(':');
          const value = valueParts.join(':').trim();
          return (
            <div key={lineIndex} className="flex flex-wrap">
              <span className="font-medium text-gray-700">{key}:</span>
              <span className="ml-1">{value}</span>
            </div>
          );
        }
        
        // Regular text
        return <div key={lineIndex}>{cleanLine}</div>;
      })}
    </div>
  );
};

export default function SoilHealthDisplay({ report, onClose }: SoilHealthDisplayProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'recommendations' | 'ai-insights' | 'trends'>('overview')

  // Helper functions
  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100'
    if (score >= 60) return 'text-yellow-600 bg-yellow-100'
    if (score >= 40) return 'text-orange-600 bg-orange-100'
    return 'text-red-600 bg-red-100'
  }

  const getHealthIcon = (score: number) => {
    if (score >= 80) return '🌱'
    if (score >= 60) return '⚠️'
    if (score >= 40) return '🔶'
    return '🚨'
  }

  const getIndicatorStatus = (value: number | undefined, optimal: { min: number; max: number }) => {
    if (value === undefined) return 'unknown'
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
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-soil-600 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">🔬 Comprehensive Soil Health Analysis</h2>
              <p className="text-soil-100 text-sm">
                Generated {new Date(report.analysis_date).toLocaleDateString()} • 
                Confidence: {(report.confidence_score * 100).toFixed(0)}% • 
                Farm ID: {report.farm_id}
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
            <nav className="flex space-x-6 px-6 overflow-x-auto">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'details', label: 'Detailed Analysis', icon: '🔍' },
                { id: 'recommendations', label: 'Recommendations', icon: '💡' },
                { id: 'ai-insights', label: 'AI Insights', icon: '🤖' },
                { id: 'trends', label: 'Trends & History', icon: '📈' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
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
                  <div className={`inline-flex items-center px-6 py-3 rounded-full text-2xl font-bold ${getHealthColor(report.health_score)}`}>
                    <span className="mr-2 text-3xl">{getHealthIcon(report.health_score)}</span>
                    {report.health_score.toFixed(0)}/100
                  </div>
                  <h3 className="mt-2 text-xl font-semibold text-gray-900 capitalize">
                    {report.overall_health} Soil Health
                  </h3>
                  <div className="text-gray-600 max-w-3xl mx-auto leading-relaxed">
                    {formatMarkdownText(report.summary)}
                  </div>
                </div>

                {/* --- Satellite Data Quality Summary --- */}
                {report.quality_summary && (
                  <div className="mt-4 flex items-center justify-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-800 border border-blue-200">
                      🛰️ Satellite Data: {report.quality_summary}
                    </span>
                    {/* Tooltip for details if issues or fallback */}
                    {(Array.isArray(report.quality_issues) && report.quality_issues.length > 0 || report.used_fallback || report.cloud_masking_status !== 'ok') && (
                      <span className="ml-2 text-xs text-gray-500" title={`Details:\n${(report.quality_issues || []).join(', ')}${report.used_fallback ? '\nUsed fallback to historical data.' : ''}${report.cloud_masking_status && report.cloud_masking_status !== 'ok' ? `\nCloud status: ${report.cloud_masking_status}` : ''}`}>
                        (details)
                      </span>
                    )}
                  </div>
                )}

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  
                  {/* Soil Chemistry */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                      🌱 Soil Chemistry
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {Object.entries(report.soil_indicators).filter(([key, value]) => {
                          const optimal = optimalRanges[key as keyof typeof optimalRanges]
                          return optimal && getIndicatorStatus(value, optimal) === 'optimal'
                        }).length}/{Object.keys(report.soil_indicators).length} Optimal
                      </span>
                    </h4>
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
                            {optimal && (
                              <div className="text-xs text-gray-500 mt-1">
                                Optimal: {optimal.min}-{optimal.max}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Vegetation Health */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                      🌿 Vegetation Health
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {Object.entries(report.vegetation_indices).filter(([key, value]) => {
                          const optimal = vegetationOptimal[key as keyof typeof vegetationOptimal]
                          return optimal && getIndicatorStatus(value, optimal) === 'optimal'
                        }).length}/{Object.keys(report.vegetation_indices).length} Optimal
                      </span>
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(report.vegetation_indices)
                        .filter(([_, value]) => value !== undefined)
                        .map(([key, value]) => {
                        const optimal = vegetationOptimal[key as keyof typeof vegetationOptimal]
                        const status = optimal ? getIndicatorStatus(value, optimal) : 'unknown'
                        return (
                          <div key={key} className={`p-2 rounded border ${getIndicatorColor(status)}`}>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium uppercase">
                                {key}
                              </span>
                              <span className="text-sm font-bold">
                                {value?.toFixed(3) ?? 'N/A'}
                              </span>
                            </div>
                            {optimal && (
                              <div className="text-xs text-gray-500 mt-1">
                                Optimal: {optimal.min}-{optimal.max}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Issues & Actions */}
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

                      <div className="p-2 rounded bg-green-50 border border-green-200">
                        <div className="text-sm font-medium text-green-800">
                          🎯 {(report.confidence_score * 100).toFixed(0)}% Confidence
                        </div>
                        <div className="text-xs text-green-600 mt-1">
                          High-quality analysis results
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Analysis Metadata */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">📋 Analysis Info</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <span className={`font-medium px-2 py-1 rounded text-xs ${
                          report.status === 'completed' ? 'bg-green-100 text-green-800' :
                          report.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {report.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Analysis ID:</span>
                        <span className="font-mono text-xs">{report.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Created:</span>
                        <span className="text-xs">{new Date(report.created_at).toLocaleDateString()}</span>
                      </div>
                      {report.trend_analysis && (
                        <div className="mt-3 p-2 bg-purple-50 border border-purple-200 rounded">
                          <div className="text-xs font-medium text-purple-800">📈 Trend Analysis Available</div>
                        </div>
                      )}
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
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">🔬 Advanced Soil Analysis</h3>
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

                {/* Detailed Soil Indicators */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white border rounded-lg p-6">
                    <h4 className="font-semibold text-gray-900 mb-4">🌱 Detailed Soil Chemistry</h4>
                    <div className="space-y-4">
                      {Object.entries(report.soil_indicators).map(([key, value]) => {
                        const optimal = optimalRanges[key as keyof typeof optimalRanges]
                        const status = optimal ? getIndicatorStatus(value, optimal) : 'unknown'
                        return (
                          <div key={key} className="border rounded-lg p-4">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium capitalize">{key.replace('_', ' ')}</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getIndicatorColor(status)}`}>
                                {status}
                              </span>
                            </div>
                            <div className="text-2xl font-bold text-gray-900 mb-1">
                              {value.toFixed(2)}{key === 'ph_level' ? '' : key === 'temperature' ? '°C' : '%'}
                            </div>
                            {optimal && (
                              <div className="text-sm text-gray-600">
                                Optimal range: {optimal.min} - {optimal.max}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="bg-white border rounded-lg p-6">
                    <h4 className="font-semibold text-gray-900 mb-4">🌿 Detailed Vegetation Analysis</h4>
                    <div className="space-y-4">
                      {Object.entries(report.vegetation_indices)
                        .filter(([_, value]) => value !== undefined)
                        .map(([key, value]) => {
                        const optimal = vegetationOptimal[key as keyof typeof vegetationOptimal]
                        const status = optimal ? getIndicatorStatus(value, optimal) : 'unknown'
                        return (
                          <div key={key} className="border rounded-lg p-4">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium uppercase">{key}</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getIndicatorColor(status)}`}>
                                {status}
                              </span>
                            </div>
                            <div className="text-2xl font-bold text-gray-900 mb-1">
                              {value?.toFixed(3) ?? 'N/A'}
                            </div>
                            {optimal && (
                              <div className="text-sm text-gray-600">
                                Optimal range: {optimal.min} - {optimal.max}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                
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

                {/* Recommendations */}
                <div>
                  <h3 className="text-lg font-semibold text-green-800 mb-4">💡 Improvement Recommendations</h3>
                  <div className="space-y-3">
                    {report.recommendations.map((recommendation, index) => (
                      <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <p className="text-sm text-green-800">{recommendation}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* AI Insights Tab */}
            {activeTab === 'ai-insights' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-4">🤖 AI Analysis Insights</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">🧠 Technical Analysis</h4>
                      <div className="text-purple-800 leading-relaxed whitespace-pre-line">
                        {(report as any).technical_analysis || "Advanced soil science analysis using satellite-derived indicators and precision agriculture methodologies. Full technical analysis includes vegetation health patterns, soil chemistry assessment, physical soil properties, environmental stress factors, and multi-temporal analysis for comprehensive soil health evaluation."}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">👨‍🌾 Farmer Summary</h4>
                      <div className="text-purple-800 leading-relaxed">
                        {formatMarkdownText((report as any).farmer_summary || "Your soil health shows areas for improvement. The most important focus right now should be on addressing pH levels and improving water management. With proper soil amendments and management practices, you can significantly enhance your farm's productivity and long-term sustainability.")}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">📊 AI Analysis Details</h4>
                      <div className="text-purple-800 leading-relaxed">
                        {(report as any).ai_explanation || "Comprehensive AI analysis combining satellite data, weather patterns, and agricultural science principles to provide actionable soil health insights."}
                      </div>
                    </div>

                    {(report as any).key_indicators_ai && (
                      <div>
                        <h4 className="font-medium text-purple-900 mb-2">🔍 Key Indicators Analysis</h4>
                        <div className="space-y-3">
                          {Object.entries((report as any).key_indicators_ai).map(([category, data]: [string, any]) => (
                            <div key={category} className="bg-purple-50 p-3 rounded border-l-4 border-purple-300">
                              <div className="font-medium text-purple-900 capitalize">{category.replace('_', ' ')}</div>
                              {typeof data === 'object' && data !== null ? (
                                <div className="text-sm text-purple-700 mt-1">
                                  {Object.entries(data).map(([key, value]: [string, any]) => (
                                    <div key={key}>
                                      <span className="font-medium">{key}:</span> {String(value)}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-sm text-purple-700 mt-1">{String(data)}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">🔬 Model Information</h4>
                      <div className="text-sm text-purple-700">
                        <p>Model Used: {(report as any).model_used || "Hybrid AI Models (Gemini + Claude)"}</p>
                        <p>AI Confidence: {((report as any).ai_confidence * 100 || report.confidence_score * 100).toFixed(1)}%</p>
                        <p>Analysis Date: {(report as any).generated_at ? new Date((report as any).generated_at).toLocaleString() : new Date(report.analysis_date).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Trends Tab */}
            {activeTab === 'trends' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-800 mb-4">📈 Historical Trends & Analysis</h3>
                  <div className="space-y-4">
                    {report.trend_analysis ? (
                      <div>
                        <h4 className="font-medium text-blue-900 mb-2">📊 Trend Analysis</h4>
                        <p className="text-blue-800 leading-relaxed">
                          {typeof report.trend_analysis === 'string' 
                            ? report.trend_analysis 
                            : JSON.stringify(report.trend_analysis, null, 2)
                          }
                        </p>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">📈</div>
                        <h4 className="font-medium text-blue-900 mb-2">Historical Data Available</h4>
                        <p className="text-blue-700">
                          Historical trend analysis will be available when multiple analyses are performed over time.
                        </p>
                      </div>
                    )}
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