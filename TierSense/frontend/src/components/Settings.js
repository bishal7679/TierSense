"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { SettingsIcon } from "lucide-react"
import ApiService from "../services/api"

const Settings = ({ onSettingsChange }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [settings, setSettings] = useState({
    llm_provider: "",
    api_key: "",
    input_source: "default",
    log_path: "/logs",
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const savedSettings = await ApiService.getSettings()
      setSettings(savedSettings)
    } catch (error) {
      console.error("Failed to load settings:", error)
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await ApiService.saveSettings(settings)
      onSettingsChange(settings)
      setIsOpen(false)
    } catch (error) {
      console.error("Failed to save settings:", error)
      alert("Failed to save settings. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <SettingsIcon className="h-4 w-4 mr-2" />
          Settings
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Configuration Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="llm-provider">LLM Provider</Label>
            <Select value={settings.llm_provider} onValueChange={(value) => handleInputChange("llm_provider", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select LLM provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="gemini">Google Gemini</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="api-key">API Key</Label>
            <Input
              id="api-key"
              type="password"
              value={settings.api_key}
              onChange={(e) => handleInputChange("api_key", e.target.value)}
              placeholder="Enter your API key"
            />
          </div>

          <div>
            <Label htmlFor="log-path">Log Path</Label>
            <Input
              id="log-path"
              value={settings.log_path}
              onChange={(e) => handleInputChange("log_path", e.target.value)}
              placeholder="/logs"
            />
          </div>

          <div>
            <Label>Input Source</Label>
            <div className="mt-2 space-y-2">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="default-source"
                  name="input-source"
                  value="default"
                  checked={settings.input_source === "default"}
                  onChange={(e) => handleInputChange("input_source", e.target.value)}
                  className="h-4 w-4 text-slate-600"
                />
                <Label htmlFor="default-source" className="text-sm font-normal">
                  Use default logs folder
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="upload-source"
                  name="input-source"
                  value="upload"
                  checked={settings.input_source === "upload"}
                  onChange={(e) => handleInputChange("input_source", e.target.value)}
                  className="h-4 w-4 text-slate-600"
                />
                <Label htmlFor="upload-source" className="text-sm font-normal">
                  Upload NDJSON file
                </Label>
              </div>
            </div>
          </div>

          <Button onClick={handleSave} disabled={loading} className="w-full">
            {loading ? "Saving..." : "Save Configuration"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default Settings
