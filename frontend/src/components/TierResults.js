import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const TierResults = ({ results }) => {
  if (!results || !results.analysis) {
    return null
  }

  const getTierColor = (tier) => {
    switch (tier) {
      case "HOT":
        return "bg-red-500"
      case "WARM":
        return "bg-yellow-500"
      case "COLD":
        return "bg-blue-500"
      default:
        return "bg-gray-500"
    }
  }

  const getTierBadgeColor = (tier) => {
    switch (tier) {
      case "HOT":
        return "bg-red-100 text-red-800"
      case "WARM":
        return "bg-yellow-100 text-yellow-800"
      case "COLD":
        return "bg-blue-100 text-blue-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-medium">Tier Classification Results</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {results.analysis.map((item, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-900 truncate">{item.path}</div>
                <div className="text-xs text-slate-500 mt-1">
                  Access: {item.access_frequency} • Score: {item.score?.toFixed(2) || "N/A"}
                  {item.size && ` • Size: ${item.size}`}
                </div>
                {item.last_accessed && (
                  <div className="text-xs text-slate-400">
                    Last accessed: {new Date(item.last_accessed).toLocaleDateString()}
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getTierColor(item.tier)}`}
                    style={{ width: `${(item.score || 0) * 100}%` }}
                  ></div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded ${getTierBadgeColor(item.tier)}`}>
                  {item.tier}
                </span>
              </div>
            </div>
          ))}
        </div>

        {results.summary && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-semibold text-slate-900">{results.summary.total_files}</div>
                <div className="text-sm text-slate-600">Total Files</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-red-600">{results.summary.hot_tier}</div>
                <div className="text-sm text-slate-600">HOT</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-yellow-600">{results.summary.warm_tier}</div>
                <div className="text-sm text-slate-600">WARM</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-blue-600">{results.summary.cold_tier}</div>
                <div className="text-sm text-slate-600">COLD</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default TierResults
