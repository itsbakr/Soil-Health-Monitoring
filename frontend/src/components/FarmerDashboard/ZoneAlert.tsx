'use client'

import { useState } from 'react'

interface ZoneAlertProps {
  zoneId: string
  health: number
  status: 'healthy' | 'moderate' | 'degraded' | 'critical'
  alerts: string[]
  primaryAction?: string
  onViewZone?: () => void
  onDismiss?: () => void
  className?: string
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'critical':
      return {
        bg: 'bg-gradient-to-r from-red-500 to-red-600',
        emoji: '🚨',
        urgency: 'Immediate action needed'
      }
    case 'degraded':
      return {
        bg: 'bg-gradient-to-r from-orange-500 to-orange-600',
        emoji: '⚠️',
        urgency: 'Attention required'
      }
    case 'moderate':
      return {
        bg: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
        emoji: '🟡',
        urgency: 'Monitor closely'
      }
    default:
      return {
        bg: 'bg-gradient-to-r from-green-500 to-green-600',
        emoji: '✅',
        urgency: 'Healthy'
      }
  }
}

export function ZoneAlert({
  zoneId,
  health,
  status,
  alerts,
  primaryAction,
  onViewZone,
  onDismiss,
  className = ''
}: ZoneAlertProps) {
  const [dismissed, setDismissed] = useState(false)
  const config = getStatusConfig(status)

  if (dismissed) return null

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss?.()
  }

  return (
    <div 
      className={`
        rounded-xl overflow-hidden shadow-lg 
        ${className}
      `}
    >
      {/* Header */}
      <div className={`${config.bg} text-white px-4 py-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">{config.emoji}</span>
            <div>
              <h3 className="font-bold">Zone {zoneId}</h3>
              <p className="text-sm opacity-90">{config.urgency}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{Math.round(health)}</div>
            <div className="text-xs opacity-90">Health</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white p-4">
        {alerts.length > 0 ? (
          <ul className="space-y-2 mb-4">
            {alerts.slice(0, 2).map((alert, idx) => (
              <li 
                key={idx}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="text-orange-500 mt-0.5">•</span>
                <span>{alert}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-600 mb-4">
            This zone has lower health scores than expected.
          </p>
        )}

        {primaryAction && (
          <p className="text-sm font-medium text-gray-900 bg-amber-50 p-2 rounded-lg mb-4">
            💡 {primaryAction}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onViewZone}
            className="flex-1 bg-gray-900 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            View Details
          </button>
          <button
            onClick={handleDismiss}
            className="py-2 px-4 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  )
}

interface ZoneAlertListProps {
  zones: Array<{
    zone_id: string
    health: number
    status: 'healthy' | 'moderate' | 'degraded' | 'critical'
    alerts: string[]
    recommendations: string[]
  }>
  onViewZone?: (zoneId: string) => void
  maxAlerts?: number
  className?: string
}

export function ZoneAlertList({ 
  zones, 
  onViewZone, 
  maxAlerts = 3,
  className = '' 
}: ZoneAlertListProps) {
  // Filter to problem zones and sort by health (worst first)
  const problemZones = zones
    .filter(z => z.health < 55)
    .sort((a, b) => a.health - b.health)
    .slice(0, maxAlerts)

  if (problemZones.length === 0) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-xl p-6 text-center ${className}`}>
        <span className="text-4xl mb-3 block">🌱</span>
        <h3 className="font-semibold text-green-800 mb-1">All Clear!</h3>
        <p className="text-sm text-green-700">All areas of your farm are healthy.</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">
          ⚠️ {problemZones.length} Area{problemZones.length > 1 ? 's' : ''} Need Attention
        </h3>
      </div>
      {problemZones.map((zone) => (
        <ZoneAlert
          key={zone.zone_id}
          zoneId={zone.zone_id}
          health={zone.health}
          status={zone.status}
          alerts={zone.alerts}
          primaryAction={zone.recommendations[0]}
          onViewZone={() => onViewZone?.(zone.zone_id)}
        />
      ))}
    </div>
  )
}

export default ZoneAlert

