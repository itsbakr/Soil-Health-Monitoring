'use client'

import { ROIAnalysisReport, CropRecommendation } from '@/lib/api'
import { useState, ReactNode } from 'react'

interface ROIDisplayProps {
  report: ROIAnalysisReport
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

// Clean markdown and return plain text (for simpler displays)
const cleanMarkdown = (text: string | undefined): string => {
  if (!text) return '';
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold markers
    .replace(/\*([^*]+)\*/g, '$1')       // Remove italic markers
    .replace(/#{1,6}\s/g, '')            // Remove headers
    .replace(/`([^`]+)`/g, '$1')         // Remove code markers
    .replace(/\n{3,}/g, '\n\n')          // Collapse multiple newlines
    .trim();
};

// Helper function to format executive summary
const _formatExecutiveSummary = (summary: string | undefined) => {
  if (!summary) return <p className="text-purple-700">Executive summary not available</p>;
  
  const sections = summary.split('**').filter(section => section.trim());
  return (
    <div className="space-y-3">
      {sections.map((section, index) => {
        if (section.includes(':')) {
          const [title, ...content] = section.split(':');
          return (
            <div key={index} className="border-b border-purple-200 pb-2 last:border-b-0">
              <h5 className="font-semibold text-purple-900 mb-1">{title.trim()}</h5>
              <p className="text-purple-700 text-sm leading-relaxed">{content.join(':').trim()}</p>
            </div>
          );
        }
        return <p key={index} className="text-purple-700 text-sm leading-relaxed">{section.trim()}</p>;
      })}
    </div>
  );
};

// Helper function to format AI reasoning
const _formatAIReasoning = (reasoning: string | undefined) => {
  if (!reasoning) return <p className="text-indigo-700">AI reasoning not available</p>;
  
  const sections = reasoning.split(/\*\*[^*]+\*\*/).filter(section => section.trim());
  const headers = reasoning.match(/\*\*[^*]+\*\*/g) || [];
  
  return (
    <div className="space-y-4">
      {headers.map((header, index) => (
        <div key={index} className="border-b border-indigo-200 pb-3 last:border-b-0">
          <h6 className="font-semibold text-indigo-900 mb-2">{header.replace(/\*\*/g, '')}</h6>
          <div className="text-indigo-700 text-sm leading-relaxed whitespace-pre-line">
            {sections[index + 1] || ''}
          </div>
        </div>
      ))}
    </div>
  );
};

// Helper function to get market trend icon
const getMarketTrendIcon = (trend: string) => {
  switch (trend?.toLowerCase()) {
    case 'upward': case 'bullish': case 'up': return '📈';
    case 'downward': case 'bearish': case 'down': return '📉';
    case 'stable': case 'neutral': return '➡️';
    case 'volatile': return '⚡';
    default: return '➡️';
  }
};

// Helper function to get weather condition icon
const getWeatherIcon = (condition: string) => {
  const conditionLower = condition?.toLowerCase() || '';
  if (conditionLower.includes('favorable') || conditionLower.includes('optimistic')) return '☀️';
  if (conditionLower.includes('challenging') || conditionLower.includes('pessimistic')) return '⛈️';
  if (conditionLower.includes('likely') || conditionLower.includes('expected')) return '⛅';
  return '🌤️';
};

// Helper function to format risk assessment
const _formatRiskAssessment = (riskText: string | undefined) => {
  if (!riskText) return <p className="text-red-700">Risk assessment not available</p>;
  
  const sections = riskText.split(/\*\*[^*]+\*\*/).filter(section => section.trim());
  const headers = riskText.match(/\*\*[^*]+\*\*/g) || [];
  
  return (
    <div className="space-y-4">
      {headers.map((header, index) => {
        const sectionContent = sections[index + 1] || '';
        const headerText = header.replace(/\*\*/g, '').trim();
        
        return (
          <div key={index} className="border-b border-red-200 pb-3 last:border-b-0">
            <h6 className="font-semibold text-red-900 mb-2 flex items-center">
              {headerText.includes('SCENARIO') && '📊 '}
              {headerText.includes('RISK FACTORS') && '⚠️ '}
              {headerText.includes('MITIGATION') && '🛡️ '}
              {headerText.includes('CONFIDENCE') && '🎯 '}
              {headerText}
            </h6>
            <div className="text-red-700 text-sm leading-relaxed">
              {sectionContent.split('•').map((item, itemIndex) => {
                if (!item.trim()) return null;
                return (
                  <div key={itemIndex} className="flex items-start mb-1">
                    {itemIndex > 0 && <span className="text-red-500 mr-2">•</span>}
                    <span>{item.trim()}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default function ROIDisplay({ report, onClose }: ROIDisplayProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'market' | 'ai-insights' | 'risk-analysis'>('overview')

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
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-crop-600 to-crop-700 text-white px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">📈 Comprehensive ROI Analysis & Crop Recommendations</h2>
              <p className="text-crop-100 text-sm">
                Generated {new Date(report.analysis_date).toLocaleDateString()} • 
                {report.crop_options?.length || 0} Crop{(report.crop_options?.length || 0) !== 1 ? 's' : ''} Analyzed • 
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
                { id: 'overview', label: 'Executive Summary', icon: '📊' },
                { id: 'recommendations', label: 'Crop Recommendations', icon: '🌾' },
                { id: 'market', label: 'Market Analysis', icon: '💹' },
                { id: 'ai-insights', label: 'AI Insights', icon: '🤖' },
                { id: 'risk-analysis', label: 'Risk Assessment', icon: '⚠️' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
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
                  <div className="text-gray-700 leading-relaxed space-y-2">
                    {formatMarkdownText(report.economic_summary || report.executive_summary || "Comprehensive economic analysis of crop options and market conditions.")}
                  </div>
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
                              <span className="text-gray-600">Expected Yield:</span>
                              <span className="font-semibold">{crop.expected_yield?.toFixed(1) || 'N/A'} bu/ac</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Input Costs:</span>
                              <span className="font-semibold">{formatCurrency(crop.input_costs)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Risk Level:</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor((crop as any).risk_level)}`}>
                                {getRiskIcon((crop as any).risk_level)} {(crop as any).risk_level || 'Moderate'}
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

                {/* Market & Weather Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Weather Forecast */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">🌦️ Weather Outlook</h4>
                    <div className="space-y-3">
                      {Object.entries(report.weather_forecast || {}).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm text-gray-600 capitalize flex items-center">
                            {getWeatherIcon(key)} {key.replace('_', ' ')}:
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {typeof value === 'string' ? value : String(value)}
                          </span>
                        </div>
                      ))}
                      {Object.keys(report.weather_forecast || {}).length === 0 && (
                        <div className="text-sm text-gray-500 italic">Weather data not available</div>
                      )}
                    </div>
                  </div>

                  {/* Market Conditions */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">💰 Market Conditions</h4>
                    <div className="space-y-2">
                      {Object.entries(report.market_forecast || {}).map(([crop, data]: [string, any]) => (
                        <div key={crop} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">{crop}:</span>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              {formatCurrency(data.price || 0)}
                            </div>
                            <div className={`text-xs flex items-center justify-end space-x-1 ${
                              data.trend === 'upward' ? 'text-green-600' : 
                              data.trend === 'downward' ? 'text-red-600' : 
                              'text-gray-500'
                            }`}>
                              <span>{getMarketTrendIcon(data.trend || 'stable')}</span>
                              <span>{data.trend || 'stable'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {Object.keys(report.market_forecast || {}).length === 0 && (
                        <div className="text-sm text-gray-500 italic">Market data not available</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* AI Reasoning */}
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-3">🤖 AI Reasoning</h3>
                  <div className="text-purple-700 leading-relaxed space-y-2">
                    {formatMarkdownText(report.reasoning || "AI-powered analysis of market conditions, soil health, and economic factors.")}
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">🌾 Detailed Crop Analysis</h3>
                
                <div className="space-y-4">
                  {(report.crop_options || []).map((crop, index) => (
                    <div key={index} className="bg-white border rounded-lg p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h4 className="text-xl font-bold text-gray-900 capitalize">
                            {crop.crop_type || crop.crop_name || `Crop ${index + 1}`}
                          </h4>
                          <div className="flex items-center space-x-4 mt-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              crop.recommendation_level === 'highly_recommended' ? 'bg-green-100 text-green-800' :
                              crop.recommendation_level === 'recommended' ? 'bg-blue-100 text-blue-800' :
                              crop.recommendation_level === 'neutral' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {crop.recommendation_level?.replace('_', ' ').toUpperCase() || 'ANALYZED'}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(crop.risk_level)}`}>
                              {getRiskIcon(crop.risk_level)} {crop.risk_level || 'Unknown Risk'}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-green-600">
                            {formatPercentage(crop.roi_percentage)}
                          </div>
                          <div className="text-sm text-gray-500">ROI</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">{formatCurrency(crop.estimated_revenue)}</div>
                          <div className="text-sm text-gray-500">Revenue</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">{formatCurrency(crop.input_costs)}</div>
                          <div className="text-sm text-gray-500">Input Costs</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{formatCurrency(crop.net_profit)}</div>
                          <div className="text-sm text-gray-500">Net Profit</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{crop.expected_yield?.toFixed(1) || 'N/A'}</div>
                          <div className="text-sm text-gray-500">Yield (bu/ac)</div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">🌱 Soil Health Impact</h5>
                          <p className="text-gray-700 text-sm">{crop.soil_health_impact || "Analysis of crop impact on long-term soil health."}</p>
                        </div>

                        {crop.implementation_steps && crop.implementation_steps.length > 0 && (
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">📋 Implementation Steps</h5>
                            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                              {crop.implementation_steps.map((step, stepIndex) => (
                                <li key={stepIndex}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {crop.risk_factors && crop.risk_factors.length > 0 && (
                          <div>
                            <h5 className="font-medium text-red-800 mb-2">⚠️ Risk Factors</h5>
                            <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                              {crop.risk_factors.map((risk, riskIndex) => (
                                <li key={riskIndex}>{risk}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {crop.mitigation_strategies && crop.mitigation_strategies.length > 0 && (
                          <div>
                            <h5 className="font-medium text-green-800 mb-2">🛡️ Mitigation Strategies</h5>
                            <ul className="list-disc list-inside text-sm text-green-700 space-y-1">
                              {crop.mitigation_strategies.map((strategy, strategyIndex) => (
                                <li key={strategyIndex}>{strategy}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {crop.reasoning && (
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">🧠 AI Reasoning</h5>
                            <p className="text-gray-700 text-sm">{crop.reasoning}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Market Analysis Tab */}
            {activeTab === 'market' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">💹 Market Analysis & Forecasts</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Market Forecast */}
                  <div className="bg-white border rounded-lg p-6">
                    <h4 className="font-semibold text-gray-900 mb-4">📈 Market Price Forecasts</h4>
                    <div className="space-y-4">
                      {Object.entries(report.market_forecast || {}).map(([crop, data]: [string, any]) => (
                        <div key={crop} className="border rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <h5 className="font-medium text-gray-900 capitalize">{crop}</h5>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              data.trend === 'increasing' ? 'bg-green-100 text-green-800' :
                              data.trend === 'decreasing' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {data.trend || 'stable'}
                            </span>
                          </div>
                          <div className="text-2xl font-bold text-gray-900 mb-1">
                            {formatCurrency(data.price || 0)}
                          </div>
                          <div className="text-sm text-gray-500">
                            Current market price per bushel
                          </div>
                          {data.forecast && (
                            <div className="mt-2 text-sm text-gray-600">
                              <strong>Forecast:</strong> {data.forecast}
                            </div>
                          )}
                        </div>
                      ))}
                      {Object.keys(report.market_forecast || {}).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <div className="text-4xl mb-4">📊</div>
                          <p>Market forecast data not available</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Weather Forecast */}
                  <div className="bg-white border rounded-lg p-6">
                    <h4 className="font-semibold text-gray-900 mb-4">🌦️ Weather Forecast</h4>
                    <div className="space-y-4">
                      {Object.entries(report.weather_forecast || {}).map(([key, value]) => (
                        <div key={key} className="border rounded-lg p-4">
                          <h5 className="font-medium text-gray-900 capitalize mb-2">
                            {key.replace('_', ' ')}
                          </h5>
                          <div className="text-lg font-semibold text-gray-900">
                            {typeof value === 'string' ? value : String(value)}
                          </div>
                        </div>
                      ))}
                      {Object.keys(report.weather_forecast || {}).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <div className="text-4xl mb-4">🌤️</div>
                          <p>Weather forecast data not available</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* AI Insights Tab */}
            {activeTab === 'ai-insights' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-purple-800 mb-4">🤖 AI Analysis Insights</h3>
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-medium text-purple-900 mb-3">📊 Executive Summary</h4>
                      <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-400">
                        {_formatExecutiveSummary(report.economic_summary)}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-purple-900 mb-3">🧠 AI Reasoning</h4>
                      <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-400">
                        {_formatAIReasoning((report as any).detailed_reasoning || report.reasoning)}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-purple-900 mb-3">👨‍🌾 Farmer Summary</h4>
                      <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-400 text-green-800">
                        {(report as any).farmer_explanation || "Farmer-friendly recommendations and implementation guidance."}
                      </div>
                    </div>

                    {(report as any).ai_insights && (
                      <div>
                        <h4 className="font-medium text-purple-900 mb-2">📊 Implementation Timeline</h4>
                        <div className="space-y-2">
                          {((report as any).ai_insights.implementation_timeline || []).map((phase: any, index: number) => (
                            <div key={index} className="bg-purple-50 p-3 rounded border-l-4 border-purple-300">
                              <div className="font-medium text-purple-900">{phase.phase}</div>
                              <div className="text-sm text-purple-700">Timeline: {phase.timeline}</div>
                              <div className="text-sm text-purple-700">Cost: {phase.cost}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">🔬 Model Information</h4>
                      <div className="text-sm text-purple-700">
                        <p>Model Used: {(report as any).model_used || "Advanced AI Models (Claude + Gemini)"}</p>
                        <p>Confidence Score: {((report as any).confidence_level * 100 || 87).toFixed(1)}%</p>
                        <p>Analysis Date: {new Date(report.analysis_date).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Risk Assessment Tab */}
            {activeTab === 'risk-analysis' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-800 mb-4">⚠️ Risk Assessment & Mitigation</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-red-900 mb-3">🛡️ Risk Analysis</h4>
                      <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
                        {_formatRiskAssessment(report.risk_assessment)}
                      </div>
                    </div>
                    
                    {(report as any).ai_insights && (report as any).ai_insights.scenario_analysis && (
                      <div>
                        <h4 className="font-medium text-red-900 mb-2">📈 Scenario Analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {Object.entries((report as any).ai_insights.scenario_analysis).map(([scenario, data]: [string, any]) => (
                            <div key={scenario} className="bg-white border rounded-lg p-4">
                              <div className="font-medium text-gray-900 mb-2 capitalize">{scenario}</div>
                              <div className="text-sm text-gray-600">
                                <p>ROI: {data.roi?.toFixed(1)}%</p>
                                <p>Probability: {(data.probability * 100)?.toFixed(0)}%</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Risk Assessment Tab */}
            {activeTab === 'risk-analysis' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-800 mb-4">⚠️ Risk Assessment & Mitigation</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-red-900 mb-2">🚨 Risk Assessment</h4>
                      <p className="text-red-800 leading-relaxed">
                        {report.risk_assessment || "Comprehensive risk analysis of crop options and market conditions."}
                      </p>
                    </div>

                    <div>
                      <h4 className="font-medium text-red-900 mb-2">📊 Risk Factors by Crop</h4>
                      <div className="space-y-3">
                        {(report.crop_options || []).map((crop, index) => (
                          <div key={index} className="bg-white border border-red-200 rounded-lg p-4">
                            <div className="flex justify-between items-center mb-2">
                              <h5 className="font-medium text-gray-900 capitalize">
                                {crop.crop_type || crop.crop_name || `Crop ${index + 1}`}
                              </h5>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(crop.risk_level)}`}>
                                {getRiskIcon(crop.risk_level)} {crop.risk_level || 'Unknown'}
                              </span>
                            </div>
                            {crop.risk_factors && crop.risk_factors.length > 0 && (
                              <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                                {crop.risk_factors.map((risk, riskIndex) => (
                                  <li key={riskIndex}>{risk}</li>
                                ))}
                              </ul>
                            )}
                            {crop.mitigation_strategies && crop.mitigation_strategies.length > 0 && (
                              <div className="mt-2">
                                <h6 className="font-medium text-green-800 text-sm">Mitigation Strategies:</h6>
                                <ul className="list-disc list-inside text-sm text-green-700 space-y-1">
                                  {crop.mitigation_strategies.map((strategy, strategyIndex) => (
                                    <li key={strategyIndex}>{strategy}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
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