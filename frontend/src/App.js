"use client"

import { useState } from "react"
import { BarChart3 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import Settings from "./components/Settings"
import RunButton from "./components/RunButton"
import TierResults from "./components/TierResults"
import Dashboard from "./components/Dashboard"

function App() {
  const [settings, setSettings] = useState({
    llm_provider: "",
    api_key: "",
    input_source: "default",
    log_path: "/logs",
  })
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleSettingsChange = (newSettings) => {
    setSettings(newSettings)
  }

  const handleAnalysisStart = () => {
    setIsAnalyzing(true)
    setAnalysisResult(null)
  }

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result)
    setIsAnalyzing(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-8 w-8 text-slate-700" />
              <h1 className="text-2xl font-semibold text-slate-900">TierSense</h1>
            </div>
            <Settings onSettingsChange={handleSettingsChange} />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Analysis Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm text-slate-600">
                    <div>
                      Provider: <span className="font-medium">{settings.llm_provider || "Not configured"}</span>
                    </div>
                    <div>
                      API Key: <span className="font-medium">{settings.api_key ? "••••••••" : "Not set"}</span>
                    </div>
                    <div>
                      Source: <span className="font-medium">{settings.input_source}</span>
                    </div>
                    {settings.input_source === "default" && (
                      <div>
                        Path: <code className="text-xs bg-gray-100 px-1 rounded">{settings.log_path}</code>
                      </div>
                    )}
                  </div>

                  <RunButton
                    settings={settings}
                    onAnalysisStart={handleAnalysisStart}
                    onAnalysisComplete={handleAnalysisComplete}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Analysis Status */}
            {isAnalyzing && (
              <Card className="mt-4">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-600 mx-auto mb-2"></div>
                    <p className="text-sm text-slate-600">Running analysis...</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {analysisResult ? (
              <div className="space-y-6">
                {/* Tier Results Summary */}
                <TierResults results={analysisResult} />

                {/* Dashboard with Heatmap and Recommendations */}
                <Dashboard analysisResult={analysisResult} />
              </div>
            ) : (
              <Card className="h-96 flex items-center justify-center">
                <div className="text-center text-slate-500">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No Analysis Results</p>
                  <p className="text-sm">Configure your settings and run an analysis to see results</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
