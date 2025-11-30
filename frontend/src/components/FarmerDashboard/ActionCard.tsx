'use client'

interface ActionCardProps {
  icon: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  zone?: string
  onClick?: () => void
  className?: string
}

const priorityConfig = {
  high: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    badge: 'bg-red-500 text-white',
    badgeText: 'Urgent'
  },
  medium: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    badge: 'bg-amber-500 text-white',
    badgeText: 'Soon'
  },
  low: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badge: 'bg-blue-500 text-white',
    badgeText: 'Suggested'
  }
}

export function ActionCard({ 
  icon, 
  title, 
  description, 
  priority, 
  zone,
  onClick,
  className = ''
}: ActionCardProps) {
  const config = priorityConfig[priority]

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-4 rounded-xl border-2 transition-all duration-200
        hover:shadow-md hover:scale-[1.02] active:scale-[0.98]
        ${config.bg} ${config.border}
        ${className}
      `}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <span className="text-2xl flex-shrink-0">{icon}</span>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 truncate">{title}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${config.badge}`}>
              {config.badgeText}
            </span>
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">{description}</p>
          {zone && (
            <span className="inline-block mt-2 text-xs bg-white px-2 py-1 rounded border border-gray-200">
              📍 Zone {zone}
            </span>
          )}
        </div>

        {/* Arrow */}
        <svg 
          className="w-5 h-5 text-gray-400 flex-shrink-0" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  )
}

interface ActionListProps {
  actions: Array<{
    icon: string
    title: string
    description: string
    priority: 'high' | 'medium' | 'low'
    zone?: string
  }>
  onActionClick?: (action: any, index: number) => void
  maxItems?: number
  className?: string
}

export function ActionList({ 
  actions, 
  onActionClick, 
  maxItems = 5,
  className = '' 
}: ActionListProps) {
  const displayActions = actions.slice(0, maxItems)

  if (displayActions.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <span className="text-4xl mb-3 block">✅</span>
        <p className="text-gray-600">No actions needed right now!</p>
        <p className="text-sm text-gray-500 mt-1">Your farm is looking great.</p>
      </div>
    )
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {displayActions.map((action, idx) => (
        <ActionCard
          key={idx}
          {...action}
          onClick={() => onActionClick?.(action, idx)}
        />
      ))}
      {actions.length > maxItems && (
        <p className="text-center text-sm text-gray-500 pt-2">
          +{actions.length - maxItems} more actions
        </p>
      )}
    </div>
  )
}

export default ActionCard

