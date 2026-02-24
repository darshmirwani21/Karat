import { useQuery } from '@tanstack/react-query'
import { getSavingsGoals } from '../services/api'
import './Goals.css'

export default function Goals() {
  const { data, isLoading } = useQuery({
    queryKey: ['savingsGoals'],
    queryFn: getSavingsGoals,
  })

  if (isLoading) {
    return <div className="goals-loading">Loading goals...</div>
  }

  return (
    <div className="goals">
      <div className="goals-header">
        <h1>Savings Goals</h1>
        <button className="btn-primary">Create New Goal</button>
      </div>

      <div className="goals-list">
        {data?.goals?.length > 0 ? (
          data.goals.map((goal: any) => (
            <div key={goal.id} className="goal-card">
              <h3>{goal.name}</h3>
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
            </div>
          ))
        ) : (
          <p className="no-goals">No savings goals yet. Create one to get started!</p>
        )}
      </div>
    </div>
  )
}

