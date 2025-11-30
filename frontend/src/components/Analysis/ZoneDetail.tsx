'use client'

import { useState } from 'react'

interface Zone {
  zone_id: string
  row: number
  col: number
  health: number
  status: 'healthy' | 'moderate' | 'degraded' | 'critical'
  ndvi: number
  ndwi: number
  moisture: number
  alerts: string[]
  recommendations: string[]
  data_quality: number
}

interface ZoneDetailProps {
  zone: Zone
  onClose: () => void
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'healthy':
      return {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-800',
        emoji: '🟢',
        label: 'Healthy'
      }
    case 'moderate':
      return {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        emoji: '🟡',
        label: 'Moderate'
      }
    case 'degraded':
      return {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-800',
        emoji: '🟠',
        label: 'Needs Attention'
      }
    case 'critical':
      return {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        emoji: '🔴',
        label: 'Critical'
      }
    default:
      return {
        bg: 'bg-gray-50',
        border: 'border-gray-200',
        text: 'text-gray-800',
        emoji: '⚪',
        label: 'Unknown'
      }
  }
}

const MetricBar = ({ label, value, max = 1, color = 'green' }: { 
  label: string
  value: number
  max?: number
  color?: string 
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  const displayValue = max === 1 ? value.toFixed(2) : `${value.toFixed(0)}%`
  
  const colorClasses = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    yellow: 'bg-yellow-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500'
  }

  // Determine color based on value if not specified
  const getAutoColor = () => {
    if (percentage >= 70) return colorClasses.green
    if (percentage >= 50) return colorClasses.yellow
    if (percentage >= 30) return colorClasses.orange
    return colorClasses.red
  }

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{displayValue}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${color === 'auto' ? getAutoColor() : colorClasses[color as keyof typeof colorClasses]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export function ZoneDetail({ zone, onClose }: ZoneDetailProps) {
  const [showMetrics, setShowMetrics] = useState(true)
  const statusConfig = getStatusConfig(zone.status)

  // Convert NDVI to percentage for display
  const ndviPercent = ((zone.ndvi + 1) / 2) * 100

  return (
    <div className={`rounded-xl border-2 ${statusConfig.border} ${statusConfig.bg} overflow-hidden`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{statusConfig.emoji}</span>
          <div>
            <h3 className="font-bold text-gray-900">Zone {zone.zone_id}</h3>
            <span className={`text-sm font-medium ${statusConfig.text}`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900">{Math.round(zone.health)}</div>
            <div className="text-xs text-gray-500">Health Score</div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close zone detail"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Metrics Toggle */}
        <button
          onClick={() => setShowMetrics(!showMetrics)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <svg 
            className={`w-4 h-4 transition-transform ${showMetrics ? 'rotate-90' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span>Technical Metrics</span>
        </button>

        {/* Metrics */}
        {showMetrics && (
          <div className="bg-white rounded-lg p-3 space-y-3 border border-gray-200">
            <MetricBar 
              label="Vegetation (NDVI)" 
              value={zone.ndvi} 
              max={1}
              color="auto"
            />
            <MetricBar 
              label="Soil Moisture" 
              value={zone.moisture} 
              max={100}
              color="auto"
            />
            <MetricBar 
              label="Water Index (NDWI)" 
              value={(zone.ndwi + 1) / 2} 
              max={1}
              color="blue"
            />
            <MetricBar 
              label="Data Quality" 
              value={zone.data_quality} 
              max={100}
              color="green"
            />
          </div>
        )}

        {/* Alerts */}
        {zone.alerts.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800 flex items-center gap-2">
              <span>⚠️</span>
              <span>Alerts</span>
            </h4>
            <ul className="space-y-1">
              {zone.alerts.map((alert, idx) => (
                <li 
                  key={idx}
                  className="bg-white rounded-lg p-2 text-sm text-gray-700 border border-amber-200"
                >
                  {alert}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {zone.recommendations.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800 flex items-center gap-2">
              <span>💡</span>
              <span>Recommendations</span>
            </h4>
            <ul className="space-y-1">
              {zone.recommendations.map((rec, idx) => (
                <li 
                  key={idx}
                  className="bg-white rounded-lg p-2 text-sm text-gray-700 border border-blue-200 flex items-start gap-2"
                >
                  <span className="text-blue-500 mt-0.5">→</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* No issues message */}
        {zone.alerts.length === 0 && zone.recommendations.length === 0 && (
          <div className="bg-white rounded-lg p-4 text-center border border-green-200">
            <span className="text-2xl mb-2 block">✅</span>
            <p className="text-sm text-gray-600">
              This area is healthy! No immediate action needed.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ZoneDetail

