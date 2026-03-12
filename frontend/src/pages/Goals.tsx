import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSavingsGoals, createGoal, generateRecommendations, approveRecommendation, getRecommendations } from '../services/api'
import './Goals.css'

interface Goal {
  id: number
  name: string
  target_amount: number
  current_amount: number
  target_date: string
}

interface Recommendation {
  id: number
  week_start: string
  recommended_amount: number
  reasoning: string
  user_approved: boolean | null
}

export default function Goals() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newGoal, setNewGoal] = useState({ name: '', targetAmount: '', targetDate: '' })
  const [expandedGoals, setExpandedGoals] = useState<Set<number>>(new Set())
  
  const queryClient = useQueryClient()

  const { data: goalsData, isLoading } = useQuery({
    queryKey: ['savingsGoals'],
    queryFn: getSavingsGoals,
  })

  const createGoalMutation = useMutation({
    mutationFn: ({ name, targetAmount, targetDate }: { name: string; targetAmount: number; targetDate: string }) =>
      createGoal(name, targetAmount, targetDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savingsGoals'] })
      setShowCreateForm(false)
      setNewGoal({ name: '', targetAmount: '', targetDate: '' })
    },
  })

  const generateRecommendationsMutation = useMutation({
    mutationFn: generateRecommendations,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(['recommendations', variables], data)
      setExpandedGoals(prev => new Set(prev).add(variables))
    },
  })

  const approveRecommendationMutation = useMutation({
    mutationFn: ({ recId, approved }: { recId: number; approved: boolean }) =>
      approveRecommendation(recId, approved),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
    },
  })

  const handleCreateGoal = (e: React.FormEvent) => {
    e.preventDefault()
    if (newGoal.name && newGoal.targetAmount && newGoal.targetDate) {
      createGoalMutation.mutate({
        name: newGoal.name,
        targetAmount: parseFloat(newGoal.targetAmount),
        targetDate: newGoal.targetDate,
      })
    }
  }

  const handleGeneratePlan = (goalId: number) => {
    generateRecommendationsMutation.mutate(goalId)
  }

  const handleApproveReject = (recId: number, approved: boolean) => {
    approveRecommendationMutation.mutate({ recId, approved })
  }

  const toggleGoalExpansion = (goalId: number) => {
    setExpandedGoals(prev => {
      const newSet = new Set(prev)
      if (newSet.has(goalId)) {
        newSet.delete(goalId)
      } else {
        newSet.add(goalId)
      }
      return newSet
    })
  }

  // Calculate total saved across all goals
  const totalSaved = goalsData?.goals?.reduce((sum, goal) => sum + goal.current_amount, 0) || 0
  const totalTarget = goalsData?.goals?.reduce((sum, goal) => sum + goal.target_amount, 0) || 0

  if (isLoading) {
    return <div className="goals-loading">Loading goals...</div>
  }

  return (
    <div className="goals">
      <div className="goals-header">
        <h1>Savings Goals</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'Create New Goal'}
        </button>
      </div>

      {/* Summary Stats */}
      <div className="goals-summary">
        <div className="summary-stat">
          <span className="stat-label">Total Saved</span>
          <span className="stat-value">${totalSaved.toFixed(2)}</span>
        </div>
        <div className="summary-stat">
          <span className="stat-label">Total Target</span>
          <span className="stat-value">${totalTarget.toFixed(2)}</span>
        </div>
        <div className="summary-stat">
          <span className="stat-label">Progress</span>
          <span className="stat-value">
            {totalTarget > 0 ? ((totalSaved / totalTarget) * 100).toFixed(1) : 0}%
          </span>
        </div>
      </div>

      {/* Create Goal Form */}
      {showCreateForm && (
        <div className="create-goal-form">
          <h3>Create New Goal</h3>
          <form onSubmit={handleCreateGoal}>
            <div className="form-group">
              <label htmlFor="goalName">Goal Name</label>
              <input
                id="goalName"
                type="text"
                value={newGoal.name}
                onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })}
                placeholder="e.g., Emergency Fund"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="targetAmount">Target Amount ($)</label>
              <input
                id="targetAmount"
                type="number"
                value={newGoal.targetAmount}
                onChange={(e) => setNewGoal({ ...newGoal, targetAmount: e.target.value })}
                placeholder="1000"
                min="1"
                step="0.01"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="targetDate">Target Date</label>
              <input
                id="targetDate"
                type="date"
                value={newGoal.targetDate}
                onChange={(e) => setNewGoal({ ...newGoal, targetDate: e.target.value })}
                min={new Date().toISOString().split('T')[0]}
                required
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={createGoalMutation.isPending}>
                {createGoalMutation.isPending ? 'Creating...' : 'Create Goal'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowCreateForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Goals List */}
      <div className="goals-list">
        {goalsData?.goals?.length > 0 ? (
          goalsData.goals.map((goal: Goal) => (
            <div key={goal.id} className="goal-card">
              <div className="goal-header">
                <h3>{goal.name}</h3>
                <button 
                  className="btn-generate-plan"
                  onClick={() => handleGeneratePlan(goal.id)}
                  disabled={generateRecommendationsMutation.isPending}
                >
                  {generateRecommendationsMutation.isPending ? 'Generating...' : 'Generate AI Plan'}
                </button>
              </div>
              
              <div className="goal-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${
                        goal.target_amount > 0
                          ? Math.min(100, (goal.current_amount / goal.target_amount) * 100)
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <p className="progress-text">
                  ${goal.current_amount.toFixed(2)} / ${goal.target_amount.toFixed(2)}
                </p>
              </div>
              <p className="goal-date">Target: {new Date(goal.target_date).toLocaleDateString()}</p>

              {/* Recommendations Section */}
              {expandedGoals.has(goal.id) && (
                <RecommendationsSection 
                  goalId={goal.id}
                  onApproveReject={handleApproveReject}
                  isApproving={approveRecommendationMutation.isPending}
                />
              )}
            </div>
          ))
        ) : (
          <p className="no-goals">No savings goals yet. Create one to get started!</p>
        )}
      </div>
    </div>
  )
}

function RecommendationsSection({ 
  goalId, 
  onApproveReject, 
  isApproving 
}: { 
  goalId: number
  onApproveReject: (recId: number, approved: boolean) => void
  isApproving: boolean 
}) {
  const { data: recommendationsData, isLoading } = useQuery({
    queryKey: ['recommendations', goalId],
    queryFn: () => getRecommendations(goalId),
    enabled: !!goalId,
  })

  if (isLoading) {
    return <div className="recommendations-loading">Loading recommendations...</div>
  }

  if (!recommendationsData?.recommendations?.length) {
    return <div className="no-recommendations">No recommendations available yet.</div>
  }

  return (
    <div className="recommendations-section">
      <h4>AI-Generated Savings Plan</h4>
      <div className="recommendations-list">
        {recommendationsData.recommendations.map((rec: Recommendation) => (
          <div key={rec.id} className={`recommendation-item ${rec.user_approved !== null ? 'decided' : ''}`}>
            <div className="recommendation-header">
              <span className="recommendation-week">
                Week starting {new Date(rec.week_start).toLocaleDateString()}
              </span>
              <span className="recommendation-amount">
                ${rec.recommended_amount.toFixed(2)}
              </span>
            </div>
            <p className="recommendation-reasoning">{rec.reasoning}</p>
            <div className="recommendation-actions">
              {rec.user_approved === null ? (
                <>
                  <button
                    className="btn-approve"
                    onClick={() => onApproveReject(rec.id, true)}
                    disabled={isApproving}
                  >
                    ✓ Approve
                  </button>
                  <button
                    className="btn-reject"
                    onClick={() => onApproveReject(rec.id, false)}
                    disabled={isApproving}
                  >
                    ✗ Reject
                  </button>
                </>
              ) : (
                <span className={`decision-status ${rec.user_approved ? 'approved' : 'rejected'}`}>
                  {rec.user_approved ? '✓ Approved' : '✗ Rejected'}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

