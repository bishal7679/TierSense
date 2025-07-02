"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Play } from "lucide-react"
import ApiService from "../services/api"

const RunButton = ({ settings, onAnalysisStart, onAnalysisComplete }) => {
  const [loading, setLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)

  const handleFileUpload = (event) => {
    const file = event.target.files?.[0]
    if (file && file.name.endsWith(".ndjson")) {
      setUploadedFile(file)
    } else {
      alert("Please select a valid .ndjson file")
    }
  }

  const handleRunAnalysis = async () => {
    if (!settings.llm_provider || !settings.api_key) {
      alert("Please configure LLM provider and API key in settings")
      return
    }

    setLoading(true)
    onAnalysisStart()

    try {
      let fileId = null

      // Upload file if using upload source
      if (settings.input_source === "upload" && uploadedFile) {
        const uploadResult = await ApiService.uploadFile(uploadedFile)
        fileId = uploadResult.file_id
      }

      // Run tiering analysis
      const analysisData = {
        llm_provider: settings.llm_provider,
        api_key: settings.api_key,
        input_source: settings.input_source,
        file_id: fileId,
        log_path: settings.log_path,
      }

      const result = await ApiService.runTiering(analysisData)
      onAnalysisComplete(result)
    } catch (error) {
      console.error("Analysis failed:", error)
      alert("Analysis failed. Please check your configuration and try again.")
    } finally {
      setLoading(false)
    }
  }

  const isConfigured = settings.llm_provider && settings.api_key
  const canRun = isConfigured && (settings.input_source === "default" || uploadedFile)

  return (
    <div className="space-y-4">
      {settings.input_source === "upload" && (
        <div>
          <Label htmlFor="file-upload">Upload NDJSON File</Label>
          <div className="mt-2">
            <input
              id="file-upload"
              type="file"
              accept=".ndjson"
              onChange={handleFileUpload}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-slate-50 file:text-slate-700 hover:file:bg-slate-100"
            />
            {uploadedFile && <p className="mt-2 text-sm text-slate-600">Selected: {uploadedFile.name}</p>}
          </div>
        </div>
      )}

      <Button onClick={handleRunAnalysis} disabled={!canRun || loading} className="w-full">
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Analyzing...
          </>
        ) : (
          <>
            <Play className="h-4 w-4 mr-2" />
            Run Analysis
          </>
        )}
      </Button>

      {!isConfigured && (
        <p className="text-sm text-red-600 text-center">Please configure settings before running analysis</p>
      )}
    </div>
  )
}

export default RunButton
