"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Download, FileText, BarChart3 } from "lucide-react"
import ApiService from "../services/api"

const Dashboard = ({ analysisResult }) => {
  const [heatmapUrl, setHeatmapUrl] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (analysisResult?.analysis_id) {
      loadHeatmap(analysisResult.analysis_id)
    }
  }, [analysisResult])

  const loadHeatmap = async (analysisId) => {
    setLoading(true)
    try {
      const heatmapBlob = await ApiService.getHeatmap(analysisId)
      const url = URL.createObjectURL(heatmapBlob)
      setHeatmapUrl(url)
    } catch (error) {
      console.error("Failed to load heatmap:", error)
    } finally {
      setLoading(false)
    }
  }

  const exportResults = () => {
    if (analysisResult) {
      const dataStr = JSON.stringify(analysisResult, null, 2)
      const dataBlob = new Blob([dataStr], { type: "application/json" })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement("a")
      link.href = url
      link.download = `tiersense-analysis-${Date.now()}.json`
      link.click()
      URL.revokeObjectURL(url)
    }
  }

  if (!analysisResult) {
    return (
      <Card className="h-96 flex items-center justify-center">
        <div className="text-center text-slate-500">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No Analysis Results</p>
          <p className="text-sm">Run an analysis to see results and heatmap visualization</p>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Heatmap Visualization */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-medium">Access Pattern Heatmap</CardTitle>
          <Button onClick={exportResults} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Results
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-600"></div>
              <span className="ml-2">Loading heatmap...</span>
            </div>
          ) : heatmapUrl ? (
            <div className="flex justify-center">
              <img
                src={heatmapUrl || "/placeholder.svg"}
                alt="File Access Heatmap"
                className="max-w-full h-auto border border-gray-200 rounded-lg"
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-500">
              <p>Heatmap not available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Storage Recommendations */}
      {analysisResult.recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">AI Storage Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysisResult.recommendations.migration_plan && (
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-2">Migration Recommendations</h4>
                  <div className="space-y-2">
                    {analysisResult.recommendations.migration_plan.map((plan, index) => (
                      <div key={index} className="border-l-4 border-slate-300 pl-4 py-2">
                        <div className="font-medium text-sm">{plan.action}</div>
                        <div className="text-sm text-slate-600">
                          {plan.files?.length || 0} files • {plan.estimated_savings}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisResult.recommendations.storage_strategy && (
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-2">Storage Strategy</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {Object.entries(analysisResult.recommendations.storage_strategy).map(([tier, config]) => (
                      <div key={tier} className="border border-gray-200 rounded-lg p-3">
                        <div className="font-medium text-sm uppercase tracking-wide mb-2">
                          {tier.replace("_tier", "")}
                        </div>
                        <div className="text-xs space-y-1">
                          <div>Storage: {config.storage_type}</div>
                          <div>
                            Location: <code className="bg-gray-100 px-1 rounded">{config.location}</code>
                          </div>
                          <div>
                            Cost: <span className="text-green-600">{config.estimated_cost}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* JSON Output */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-medium flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            Raw JSON Output
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={JSON.stringify(analysisResult, null, 2)}
            readOnly
            className="font-mono text-sm h-64 resize-none"
          />
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard
