'use client'

import { ROIAnalysisReport, CropRecommendation } from '@/lib/api'
import { useState } from 'react'

interface ROIDisplayProps {
  report: ROIAnalysisReport
  onClose?: () => void
}

export default function ROIDisplay({ report, onClose }: ROIDisplayProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'market'>('overview')

  // Helper functions
  const getRiskColor = (riskLevel: string | undefined) => {
    if (!riskLevel) return 'text-gray-600 bg-gray-100'
    switch (riskLevel.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100'
      case 'moderate': return 'text-yellow-600 bg-yellow-100'
      case 'high': return 'text-red-600 bg-red-100'
      case 'critical': return 'text-red-800 bg-red-200'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getRiskIcon = (riskLevel: string | undefined) => {
    if (!riskLevel) return '⚪'
    switch (riskLevel.toLowerCase()) {
      case 'low': return '🟢'
      case 'moderate': return '🟡'
      case 'high': return '🟠'
      case 'critical': return '🔴'
      default: return '⚪'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  const getTopRecommendations = (recommendations: CropRecommendation[], count: number = 3) => {
    return recommendations
      .sort((a, b) => b.roi_percentage - a.roi_percentage)
      .slice(0, count)
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-crop-600 to-crop-700 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">📈 ROI Analysis & Crop Recommendations</h2>
              <p className="text-crop-100 text-sm">
                Generated {new Date(report.analysis_date).toLocaleDateString()} • 
                {report.crop_options?.length || 0} Crop{(report.crop_options?.length || 0) !== 1 ? 's' : ''} Analyzed
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
                { id: 'overview', label: 'Executive Summary', icon: '📊' },
                { id: 'recommendations', label: 'Crop Recommendations', icon: '🌾' },
                { id: 'market', label: 'Market Analysis', icon: '💹' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-crop-500 text-crop-600'
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
                
                {/* Executive Summary */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">🎯 Executive Summary</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {report.economic_summary || report.executive_summary}
                  </p>
                </div>

                {/* Top 3 Recommendations */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">🏆 Top Crop Recommendations</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {getTopRecommendations(report.crop_options || []).map((crop, index) => (
                                              <div key={crop.crop_type || crop.crop_name || `crop-${index}`} className="bg-white border rounded-lg p-4 relative overflow-hidden">
                        
                        {/* Rank Badge */}
                        <div className="absolute top-2 right-2">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            index === 0 ? 'bg-yellow-100 text-yellow-800' : 
                            index === 1 ? 'bg-gray-100 text-gray-700' : 
                            'bg-orange-100 text-orange-800'
                          }`}>
                            #{index + 1}
                          </div>
                        </div>

                        <div className="pr-10">
                          <h4 className="text-lg font-bold text-gray-900 capitalize mb-2">
                            {crop.crop_type || crop.crop_name || 'Unknown Crop'}
                          </h4>
                          
                          {/* ROI */}
                          <div className="mb-3">
                            <div className="text-2xl font-bold text-green-600">
                              {formatPercentage(crop.roi_percentage)}
                            </div>
                            <div className="text-sm text-gray-500">Expected ROI</div>
                          </div>

                          {/* Key Metrics */}
                          <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Net Profit:</span>
                              <span className="font-semibold">{formatCurrency(crop.net_profit)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Payback:</span>
                              <span className="font-semibold">{crop.payback_period || 'N/A'} months</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Risk:</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(crop.risk_level)}`}>
                                {getRiskIcon(crop.risk_level)} {crop.risk_level || 'Unknown'}
                              </span>
                            </div>
                          </div>

                          {/* Confidence Bar */}
                          <div className="mt-3">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>AI Confidence</span>
                              <span>{formatPercentage(crop.confidence_score * 100)}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${crop.confidence_score * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Risk Assessment Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Weather Forecast */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">🌦️ Weather Outlook</h4>
                    <div className="space-y-2">
                      {Object.entries(report.weather_forecast).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">
                            {key.replace('_', ' ')}:
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {typeof value === 'string' ? value : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Market Conditions */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">💰 Market Conditions</h4>
                    <div className="space-y-2">
                      {Object.entries(report.market_forecast).map(([crop, data]: [string, any]) => (
                        <div key={crop} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">{crop}:</span>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              {formatCurrency(data.price || 0)}
                            </div>
                            <div className={`text-xs ${
                              data.trend === 'increasing' ? 'text-green-600' : 
                              data.trend === 'decreasing' ? 'text-red-600' : 
                              'text-gray-500'
                            }`}>
                              {data.trend || 'stable'}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Farmer Recommendations */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-800 mb-3">👨‍🌾 Farmer Recommendations</h3>
                  <p className="text-green-700 leading-relaxed">
                    {report.farmer_recommendations}
                  </p>
                </div>
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">🌾 Detailed Crop Analysis</h3>
                
                <div className="space-y-4">
                  {(report.crop_options || []).map((crop, index) => (
                                          <div key={crop.crop_type || crop.crop_name || `crop-detail-${index}`} className="bg-white border rounded-lg p-6">
                      
                      {/* Header */}
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="text-xl font-bold text-gray-900 capitalize">
                            {crop.crop_name}
                          </h4>
                          <p className="text-sm text-gray-500">
                            Rank #{index + 1} • {formatPercentage(crop.roi_percentage)} ROI
                          </p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(crop.risk_level)}`}>
                          {getRiskIcon(crop.risk_level)} {crop.risk_level} Risk
                        </div>
                      </div>

                      {/* Financial Metrics */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div className="text-center p-3 bg-gray-50 rounded">
                          <div className="text-lg font-bold text-gray-900">
                            {formatCurrency(crop.estimated_revenue || 0)}
                          </div>
                          <div className="text-xs text-gray-500">Expected Revenue</div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded">
                          <div className="text-lg font-bold text-gray-900">
                            {formatCurrency(crop.input_costs)}
                          </div>
                          <div className="text-xs text-gray-500">Input Costs</div>
                        </div>
                        <div className="text-center p-3 bg-green-50 rounded">
                          <div className="text-lg font-bold text-green-600">
                            {formatCurrency(crop.net_profit)}
                          </div>
                          <div className="text-xs text-gray-500">Net Profit</div>
                        </div>
                        <div className="text-center p-3 bg-blue-50 rounded">
                          <div className="text-lg font-bold text-blue-600">
                            {crop.payback_period}m
                          </div>
                          <div className="text-xs text-gray-500">Payback Period</div>
                        </div>
                      </div>

                      {/* Compatibility Scores */}
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Soil Compatibility</span>
                            <span className="font-medium">{formatPercentage((crop.soil_compatibility || 0) * 100)}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full transition-all"
                              style={{ width: `${(crop.soil_compatibility || 0) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Market Favorability</span>
                            <span className="font-medium">{formatPercentage((crop.market_favorability || 0) * 100)}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full transition-all"
                              style={{ width: `${(crop.market_favorability || 0) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>

                      {/* AI Reasoning */}
                      <div className="mb-4">
                        <h5 className="font-medium text-gray-900 mb-2">🧠 AI Analysis</h5>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {crop.reasoning}
                        </p>
                      </div>

                                              {/* Implementation Steps */}
                        {(crop.implementation_steps?.length || 0) > 0 && (
                          <div className="mb-4">
                            <h5 className="font-medium text-gray-900 mb-2">✅ Implementation Steps</h5>
                            <ol className="list-decimal list-inside space-y-1">
                              {(crop.implementation_steps || []).map((step, stepIndex) => (
                                <li key={stepIndex} className="text-sm text-gray-700">{step}</li>
                              ))}
                            </ol>
                          </div>
                        )}

                      {/* Risk Factors */}
                      {(crop.risk_factors?.length || 0) > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium text-red-800 mb-2">⚠️ Risk Factors</h5>
                            <ul className="space-y-1">
                              {(crop.risk_factors || []).map((risk, riskIndex) => (
                                <li key={riskIndex} className="text-sm text-red-700 flex items-start">
                                  <span className="mr-1">•</span>
                                  {risk}
                                </li>
                              ))}
                            </ul>
                          </div>
                          
                          {/* Mitigation Strategies */}
                          {(crop.mitigation_strategies?.length || 0) > 0 && (
                            <div>
                              <h5 className="font-medium text-green-800 mb-2">🛡️ Mitigation Strategies</h5>
                              <ul className="space-y-1">
                                {(crop.mitigation_strategies || []).map((strategy, strategyIndex) => (
                                  <li key={strategyIndex} className="text-sm text-green-700 flex items-start">
                                    <span className="mr-1">•</span>
                                    {strategy}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Market Tab */}
            {activeTab === 'market' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">💹 Market Analysis & Decision Matrix</h3>
                
                {/* Decision Matrix */}
                <div className="bg-white border rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">📊 Decision Matrix</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full table-auto">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-900">Crop</th>
                          <th className="px-4 py-2 text-center text-sm font-medium text-gray-900">ROI %</th>
                          <th className="px-4 py-2 text-center text-sm font-medium text-gray-900">Risk</th>
                          <th className="px-4 py-2 text-center text-sm font-medium text-gray-900">Soil Match</th>
                          <th className="px-4 py-2 text-center text-sm font-medium text-gray-900">Market</th>
                          <th className="px-4 py-2 text-center text-sm font-medium text-gray-900">Confidence</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {(report.crop_options || []).map((crop, index) => (
                          <tr key={crop.crop_type || crop.crop_name || `crop-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-4 py-2 font-medium text-gray-900 capitalize">
                              {crop.crop_type || crop.crop_name || 'Unknown Crop'}
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className="font-bold text-green-600">
                                {formatPercentage(crop.roi_percentage)}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(crop.risk_level)}`}>
                                {crop.risk_level}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className="font-medium">
                                {formatPercentage((crop.soil_compatibility || 0) * 100)}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className="font-medium">
                                {formatPercentage((crop.market_favorability || 0) * 100)}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className="font-medium">
                                {formatPercentage(crop.confidence_score * 100)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Analysis Metadata */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">📋 Analysis Details</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
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