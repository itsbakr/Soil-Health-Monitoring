'use client'

import { useState, useEffect } from 'react'
import { getAnalysisHistory, AnalysisHistoryResponse, AnalysisHistorySoilHealth, AnalysisHistoryROI } from '@/lib/api'

interface AnalysisHistoryProps {
  farmId: string
  onSelectAnalysis?: (analysis: AnalysisHistorySoilHealth | AnalysisHistoryROI, type: 'soil' | 'roi') => void
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getHealthColor = (score: number) => {
  if (score >= 75) return 'text-green-600 bg-green-100'
  if (score >= 55) return 'text-yellow-600 bg-yellow-100'
  if (score >= 35) return 'text-orange-600 bg-orange-100'
  return 'text-red-600 bg-red-100'
}

const getHealthEmoji = (score: number) => {
  if (score >= 75) return '🟢'
  if (score >= 55) return '🟡'
  if (score >= 35) return '🟠'
  return '🔴'
}

export default function AnalysisHistory({ farmId, onSelectAnalysis }: AnalysisHistoryProps) {
  const [history, setHistory] = useState<AnalysisHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'all' | 'soil' | 'roi'>('all')

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await getAnalysisHistory(farmId, 20)
        setHistory(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load analysis history')
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [farmId])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center text-red-600">
          <span className="text-2xl mb-2 block">⚠️</span>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  if (!history || history.total_analyses === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center text-gray-500 py-8">
          <span className="text-4xl mb-4 block">📊</span>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis History</h3>
          <p className="text-sm">Run your first analysis to start building your farm's history.</p>
        </div>
      </div>
    )
  }

  // Combine and sort all analyses by date
  const allAnalyses = [
    ...history.soil_health.map(a => ({ ...a, type: 'soil' as const })),
    ...history.roi.map(a => ({ ...a, type: 'roi' as const }))
  ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  const filteredAnalyses = activeTab === 'all' 
    ? allAnalyses 
    : allAnalyses.filter(a => a.type === (activeTab === 'soil' ? 'soil' : 'roi'))

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          📜 Analysis History
          <span className="bg-white/20 px-2 py-0.5 rounded-full text-sm">
            {history.total_analyses} total
          </span>
        </h3>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          {[
            { id: 'all', label: 'All', count: allAnalyses.length },
            { id: 'soil', label: '🌱 Soil Health', count: history.soil_health.length },
            { id: 'roi', label: '💰 ROI', count: history.roi.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              <span className="ml-2 bg-gray-100 px-2 py-0.5 rounded-full text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Analysis List */}
      <div className="divide-y divide-gray-200 max-h-[500px] overflow-y-auto">
        {filteredAnalyses.map((analysis) => (
          <div
            key={`${analysis.type}-${analysis.id}`}
            className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
            onClick={() => onSelectAnalysis?.(analysis as any, analysis.type)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                {/* Type Icon */}
                <div className={`p-2 rounded-lg ${
                  analysis.type === 'soil' 
                    ? 'bg-green-100 text-green-600' 
                    : 'bg-blue-100 text-blue-600'
                }`}>
                  {analysis.type === 'soil' ? '🌱' : '💰'}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">
                      {analysis.type === 'soil' ? 'Soil Health Analysis' : 'ROI Analysis'}
                    </h4>
                    {analysis.type === 'soil' && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        getHealthColor((analysis as AnalysisHistorySoilHealth).overall_health)
                      }`}>
                        {getHealthEmoji((analysis as AnalysisHistorySoilHealth).overall_health)}
                        {' '}
                        {(analysis as AnalysisHistorySoilHealth).overall_health?.toFixed(0)}%
                      </span>
                    )}
                    {analysis.type === 'roi' && (analysis as AnalysisHistoryROI).projected_profit && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        (analysis as AnalysisHistoryROI).projected_profit > 0 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        ${(analysis as AnalysisHistoryROI).projected_profit?.toLocaleString() || '0'}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-500 mt-1">
                    {formatDate(analysis.created_at)}
                  </p>

                  {/* Summary preview */}
                  {analysis.type === 'soil' && (analysis as AnalysisHistorySoilHealth).ai_summary && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {(analysis as AnalysisHistorySoilHealth).ai_summary.substring(0, 150)}...
                    </p>
                  )}
                  {analysis.type === 'roi' && (analysis as AnalysisHistoryROI).ai_summary && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {(analysis as AnalysisHistoryROI).ai_summary.substring(0, 150)}...
                    </p>
                  )}

                  {/* Quick stats */}
                  {analysis.type === 'soil' && (
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      {(analysis as AnalysisHistorySoilHealth).ndvi && (
                        <span>NDVI: {(analysis as AnalysisHistorySoilHealth).ndvi?.toFixed(3)}</span>
                      )}
                      {(analysis as AnalysisHistorySoilHealth).problem_zones?.length > 0 && (
                        <span className="text-orange-600">
                          ⚠️ {(analysis as AnalysisHistorySoilHealth).problem_zones.length} problem zones
                        </span>
                      )}
                    </div>
                  )}
                  {analysis.type === 'roi' && (analysis as AnalysisHistoryROI).current_crop && (
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      <span>Crop: {(analysis as AnalysisHistoryROI).current_crop}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Status badge */}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                analysis.status === 'completed'
                  ? 'bg-green-100 text-green-700'
                  : analysis.status === 'failed'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {analysis.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      {filteredAnalyses.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-center">
          <p className="text-xs text-gray-500">
            Showing {filteredAnalyses.length} analyses • Click to view details
          </p>
        </div>
      )}
    </div>
  )
}

