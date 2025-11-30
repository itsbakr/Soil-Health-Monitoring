'use client'

import { useEffect, useState } from 'react'

interface HealthGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  animated?: boolean
  className?: string
}

const getHealthConfig = (score: number) => {
  if (score >= 75) {
    return {
      color: '#22c55e', // green-500
      bgColor: '#dcfce7', // green-100
      label: 'Healthy',
      emoji: '🌱'
    }
  }
  if (score >= 55) {
    return {
      color: '#eab308', // yellow-500
      bgColor: '#fef9c3', // yellow-100
      label: 'Moderate',
      emoji: '🌿'
    }
  }
  if (score >= 35) {
    return {
      color: '#f97316', // orange-500
      bgColor: '#ffedd5', // orange-100
      label: 'Needs Attention',
      emoji: '⚠️'
    }
  }
  return {
    color: '#ef4444', // red-500
    bgColor: '#fee2e2', // red-100
    label: 'Critical',
    emoji: '🚨'
  }
}

const sizeConfig = {
  sm: { width: 80, strokeWidth: 6, fontSize: '1rem', labelSize: '0.65rem' },
  md: { width: 120, strokeWidth: 8, fontSize: '1.5rem', labelSize: '0.75rem' },
  lg: { width: 180, strokeWidth: 10, fontSize: '2.5rem', labelSize: '0.875rem' }
}

export function HealthGauge({ 
  score, 
  size = 'md', 
  showLabel = true, 
  animated = true,
  className = ''
}: HealthGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(animated ? 0 : score)
  const config = getHealthConfig(score)
  const { width, strokeWidth, fontSize, labelSize } = sizeConfig[size]
  
  const radius = (width - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (animatedScore / 100) * circumference

  useEffect(() => {
    if (!animated) {
      setAnimatedScore(score)
      return
    }

    // Animate the score
    const duration = 1000 // 1 second
    const steps = 60
    const increment = score / steps
    let current = 0
    
    const timer = setInterval(() => {
      current += increment
      if (current >= score) {
        setAnimatedScore(score)
        clearInterval(timer)
      } else {
        setAnimatedScore(current)
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [score, animated])

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width, height: width }}>
        {/* Background circle */}
        <svg 
          width={width} 
          height={width} 
          className="transform -rotate-90"
        >
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="transparent"
            stroke={config.bgColor}
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="transparent"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
          />
        </svg>
        
        {/* Center content */}
        <div 
          className="absolute inset-0 flex flex-col items-center justify-center"
        >
          <span className="mb-0.5">{config.emoji}</span>
          <span 
            className="font-bold"
            style={{ fontSize, color: config.color }}
          >
            {Math.round(animatedScore)}
          </span>
        </div>
      </div>
      
      {showLabel && (
        <span 
          className="mt-2 font-medium text-gray-700"
          style={{ fontSize: labelSize }}
        >
          {config.label}
        </span>
      )}
    </div>
  )
}

export default HealthGauge

