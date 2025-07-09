"use client";

import type React from "react";
import { useState, useEffect } from "react";
import { Download, Settings, BarChart3, FileText, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { llmOptions } from "@/src/config/llmOptions";

// Mock data for demonstration
const mockResults = {
  analysis: [
    {
      path: "/data/logs/app-2024-01.log",
      tier: "HOT",
      score: 0.95,
      access_frequency: "daily",
    },
    {
      path: "/data/logs/app-2024-02.log",
      tier: "WARM",
      score: 0.67,
      access_frequency: "weekly",
    },
    {
      path: "/data/logs/app-2023-12.log",
      tier: "COLD",
      score: 0.23,
      access_frequency: "monthly",
    },
    {
      path: "/data/backups/db-backup-2024.sql",
      tier: "COLD",
      score: 0.15,
      access_frequency: "rarely",
    },
    {
      path: "/data/cache/temp-files/",
      tier: "HOT",
      score: 0.89,
      access_frequency: "hourly",
    },
  ],
  summary: {
    total_files: 5,
    hot_tier: 2,
    warm_tier: 1,
    cold_tier: 2,
  },
};

// Add mock recommendations data after the mockResults object
const mockRecommendations = {
  storage_strategy: {
    hot_tier: {
      storage_type: "NVMe SSD",
      location: "/fast-storage/hot-data/",
      backup_frequency: "Real-time",
      retention_policy: "6 months",
      estimated_cost: "$0.23/GB/month",
    },
    warm_tier: {
      storage_type: "SATA SSD",
      location: "/standard-storage/warm-data/",
      backup_frequency: "Daily",
      retention_policy: "2 years",
      estimated_cost: "$0.10/GB/month",
    },
    cold_tier: {
      storage_type: "HDD/Cloud Archive",
      location: "/archive-storage/cold-data/",
      backup_frequency: "Weekly",
      retention_policy: "7 years",
      estimated_cost: "$0.004/GB/month",
    },
  },
  migration_plan: [
    {
      action: "Move to hot storage",
      files: ["/data/logs/app-2024-01.log", "/data/cache/temp-files/"],
      priority: "High",
      estimated_savings: "15% performance improvement",
    },
    {
      action: "Archive to cold storage",
      files: ["/data/logs/app-2023-12.log", "/data/backups/db-backup-2024.sql"],
      priority: "Medium",
      estimated_savings: "$45/month storage cost reduction",
    },
  ],
  optimization_summary: {
    total_cost_savings: "$67/month",
    performance_improvement: "23%",
    storage_efficiency: "89%",
  },
};

export default function TierSense() {
  const [selectedLLM, setSelectedLLM] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [inputSource, setInputSource] = useState("default");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<typeof mockResults | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // 💾 Load API key from localStorage on mount
  useEffect(() => {
    const savedKey = localStorage.getItem("tiersense_api_key");
    if (savedKey) setApiKey(savedKey);
  }, []);

  // 💾 Save API key to localStorage on change
  useEffect(() => {
    if (apiKey) localStorage.setItem("tiersense_api_key", apiKey);
  }, [apiKey]);

  const handleRunAnalysis = async () => {
    try {
      const formData = new FormData();
      formData.append("llm", selectedLLM);
      formData.append("api_key", apiKey);
      if (inputSource === "upload") {
        if (!uploadedFile) {
          throw new Error("Please select and upload a valid .ndjson file.");
        }
        formData.append("file", uploadedFile);
      }

      const response = await fetch(
        "http://10.14.220.29:8000/api/run-tiering",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error) {
      console.error("Failed to fetch:", error);
      // alert("Run failed: " + error.message)
    }
  };
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith(".ndjson")) {
      setUploadedFile(file);
    }
  };

  const exportResults = () => {
    if (results) {
      const dataStr = JSON.stringify(results, null, 2);
      const dataBlob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "tiersense-analysis.json";
      link.click();
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "HOT":
        return "bg-red-500";
      case "WARM":
        return "bg-yellow-500";
      case "COLD":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-8 w-8 text-slate-700" />
              <h1 className="text-2xl font-semibold text-slate-900">
                TierSense
              </h1>
            </div>
            <Dialog open={showSettings} onOpenChange={setShowSettings}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>API Configuration</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="settings-api-key">API Key</Label>
                    <Input
                      id="settings-api-key"
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your API key"
                    />
                  </div>
                  <Button
                    onClick={() => setShowSettings(false)}
                    className="w-full"
                  >
                    Save Configuration
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">
                  Analysis Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="llm-select">LLM Provider</Label>
                  <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose Model" />
                    </SelectTrigger>
                    <SelectContent>
                      {llmOptions.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="api-key">API Key</Label>
                  <Input
                    id="api-key"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter API key"
                  />
                </div>

                <div>
                  <Label>Data Source</Label>
                  <div className="mt-2 space-y-3">
                    <div className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id="default-logs"
                        name="input-source"
                        value="default"
                        checked={inputSource === "default"}
                        onChange={(e) => setInputSource(e.target.value)}
                        className="h-4 w-4 text-slate-600"
                      />
                      <Label
                        htmlFor="default-logs"
                        className="text-sm font-normal"
                      >
                        Use default /logs folder
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id="upload-file"
                        name="input-source"
                        value="upload"
                        checked={inputSource === "upload"}
                        onChange={(e) => setInputSource(e.target.value)}
                        className="h-4 w-4 text-slate-600"
                      />
                      <Label
                        htmlFor="upload-file"
                        className="text-sm font-normal"
                      >
                        Upload .ndjson file
                      </Label>
                    </div>
                  </div>
                </div>

                {inputSource === "upload" && (
                  <div>
                    <Label htmlFor="file-upload">Upload File</Label>
                    <div className="mt-2">
                      <input
                        id="file-upload"
                        type="file"
                        accept=".ndjson"
                        onChange={handleFileUpload}
                        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-slate-50 file:text-slate-700 hover:file:bg-slate-100"
                      />
                      {uploadedFile && (
                        <p className="mt-2 text-sm text-slate-600">
                          Selected: {uploadedFile.name}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <Button
                  onClick={handleRunAnalysis}
                  disabled={!selectedLLM || !apiKey || isAnalyzing}
                  className="w-full"
                >
                  {isAnalyzing ? (
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
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {results ? (
              <div className="space-y-6">
                {/* Summary */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-lg font-medium">
                      Analysis Summary
                    </CardTitle>
                    <Button onClick={exportResults} variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-slate-900">
                          {results?.summary?.total_files ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">
                          Total Files
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-red-600">
                          {results?.summary?.hot_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">HOT</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-yellow-600">
                          {results?.summary?.warm_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">WARM</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-blue-600">
                          {results?.summary?.cold_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">COLD</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg font-medium">Access Heatmap</CardTitle>
                  </CardHeader>
                  <CardContent className="text-center">
                    <img
                      src={`http://10.14.220.29:8000/api/heatmap?ts=${Date.now()}`}
                      alt="Heatmap"
                      className="mx-auto rounded border border-gray-300"
                      style={{ maxHeight: "500px", objectFit: "contain" }}
                    />
                  </CardContent>
                </Card>

                {/* AI Storage Recommendations */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg font-medium flex items-center">
                      <Settings className="h-5 w-5 mr-2" />
                      AI Storage Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Storage Strategy */}
                    <div>
                      <h4 className="text-sm font-medium text-slate-900 mb-3">
                        Recommended Storage Configuration
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(
                          mockRecommendations.storage_strategy
                        ).map(([tier, config]) => (
                          <div
                            key={tier}
                            className="border border-gray-200 rounded-lg p-4"
                          >
                            <div className="flex items-center mb-2">
                              <div
                                className={`w-3 h-3 rounded-full mr-2 ${
                                  tier === "hot_tier"
                                    ? "bg-red-500"
                                    : tier === "warm_tier"
                                    ? "bg-yellow-500"
                                    : "bg-blue-500"
                                }`}
                              ></div>
                              <span className="font-medium text-sm uppercase tracking-wide">
                                {tier.replace("_tier", "")}
                              </span>
                            </div>
                            <div className="space-y-2 text-sm">
                              <div>
                                <span className="text-slate-600">Storage:</span>
                                <span className="ml-1 font-medium">
                                  {config.storage_type}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">
                                  Location:
                                </span>
                                <code className="ml-1 text-xs bg-gray-100 px-1 py-0.5 rounded">
                                  {config.location}
                                </code>
                              </div>
                              <div>
                                <span className="text-slate-600">Backup:</span>
                                <span className="ml-1">
                                  {config.backup_frequency}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-600">Cost:</span>
                                <span className="ml-1 font-medium text-green-600">
                                  {config.estimated_cost}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Migration Plan */}
                    <div>
                      <h4 className="text-sm font-medium text-slate-900 mb-3">
                        Migration Action Plan
                      </h4>
                      <div className="space-y-3">
                        {mockRecommendations.migration_plan.map(
                          (plan, index) => (
                            <div
                              key={index}
                              className="border-l-4 border-slate-300 pl-4 py-2"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-sm">
                                  {plan.action}
                                </span>
                                <span
                                  className={`px-2 py-1 text-xs rounded ${
                                    plan.priority === "High"
                                      ? "bg-red-100 text-red-700"
                                      : plan.priority === "Medium"
                                      ? "bg-yellow-100 text-yellow-700"
                                      : "bg-green-100 text-green-700"
                                  }`}
                                >
                                  {plan.priority} Priority
                                </span>
                              </div>
                              <div className="text-sm text-slate-600 mb-1">
                                Files: {plan.files.length} items
                              </div>
                              <div className="text-sm text-green-600 font-medium">
                                Expected benefit: {plan.estimated_savings}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>

                    {/* Optimization Summary */}
                    <div className="bg-slate-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-slate-900 mb-3">
                        Optimization Impact
                      </h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-lg font-semibold text-green-600">
                            {
                              mockRecommendations.optimization_summary
                                .total_cost_savings
                            }
                          </div>
                          <div className="text-xs text-slate-600">
                            Cost Savings
                          </div>
                        </div>
                        <div>
                          <div className="text-lg font-semibold text-blue-600">
                            {
                              mockRecommendations.optimization_summary
                                .performance_improvement
                            }
                          </div>
                          <div className="text-xs text-slate-600">
                            Performance Gain
                          </div>
                        </div>
                        <div>
                          <div className="text-lg font-semibold text-purple-600">
                            {
                              mockRecommendations.optimization_summary
                                .storage_efficiency
                            }
                          </div>
                          <div className="text-xs text-slate-600">
                            Storage Efficiency
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* JSON Output */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg font-medium flex items-center">
                      <FileText className="h-5 w-5 mr-2" />
                      JSON Output
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      value={JSON.stringify(results, null, 2)}
                      readOnly
                      className="font-mono text-sm h-64 resize-none"
                    />
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="h-96 flex items-center justify-center">
                <div className="text-center text-slate-500">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No Analysis Results</p>
                  <p className="text-sm">
                    Configure your settings and run an analysis to see results
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
