"use client";

import React, { useState, useEffect } from "react";
import {
  Download,
  Settings,
  BarChart3,
  FileText,
  Play,
  Eye,
  EyeOff,
  Filter,
  Search,
  Calendar,
  RefreshCw,
  Activity,
  Zap,
  Github,
  Twitter,
  Linkedin,
  Mail,
  Building2,
  Shield,
  TrendingUp,
} from "lucide-react";
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

export default function TierSense() {
  // Core state
  const [selectedLLM, setSelectedLLM] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<any | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeyWarning, setApiKeyWarning] = useState("");
  const [selectedDirectory, setSelectedDirectory] = useState("");

  // Tier ranges (HOT, WARM, COLD)
  const [tierRanges, setTierRanges] = useState<{ [key: string]: [number | null, number | null] }>({
    HOT: [100, null],
    WARM: [20, 99],
    COLD: [null, 19],
  });
  const [tierError, setTierError] = useState("");

  // Daily reset and historical state
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [heatmapUrl, setHeatmapUrl] = useState("");
  const [dailyResetInfo, setDailyResetInfo] = useState<any>(null);

  // Enhanced search/filter state
  const [searchType, setSearchType] = useState("current");
  const [selectedDate, setSelectedDate] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filePattern, setFilePattern] = useState("");
  const [topN, setTopN] = useState(50);
  const [isSearching, setIsSearching] = useState(false);

  // Summary counts
  const [totalFiles, setTotalFiles] = useState<number | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load API key and dates on mount
  useEffect(() => {
    const savedKey = localStorage.getItem("tiersense_api_key");
    if (savedKey) setApiKey(savedKey);
    fetchAvailableDates();
  }, []);

  // Persist API key
  useEffect(() => {
    if (apiKey) localStorage.setItem("tiersense_api_key", apiKey);
  }, [apiKey]);

  // Load settings including tierRanges when dialog opens
  useEffect(() => {
    if (showSettings) {
      fetch(`${apiUrl}/api/settings`)
        .then((res) => res.json())
        .then((data) => {
          if (data.api_key) setApiKey(data.api_key);
          if (data.default_llm) setSelectedLLM(data.default_llm);
          if (data.tier_ranges) setTierRanges(data.tier_ranges);
        })
        .catch(console.error);
    }
  }, [showSettings]);

  // Fetch available historical dates
  const fetchAvailableDates = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/historical-dates`);
      if (response.ok) {
        const data = await response.json();
        setAvailableDates(data.available_dates || []);
      }
    } catch (error) {
      console.error("Failed to fetch available dates:", error);
    }
  };

  // Advanced search handler
  const handleAdvancedSearch = async () => {
    setIsSearching(true);
    setApiKeyWarning("");

    try {
      const formData = new FormData();
      formData.append("search_type", searchType);
      formData.append("top_n", topN.toString());

      if (selectedDirectory) {
        const monitorPath = selectedDirectory.startsWith("/host-root")
          ? selectedDirectory
          : `/host-root${selectedDirectory.startsWith("/") ? selectedDirectory : `/${selectedDirectory}`}`;
        formData.append("directory", monitorPath);
      }

      if (searchType === "date" && selectedDate) {
        formData.append("date", selectedDate);
      } else if (searchType === "range" && startDate && endDate) {
        formData.append("start_date", startDate);
        formData.append("end_date", endDate);
      } else if (searchType === "pattern" && filePattern) {
        formData.append("file_pattern", filePattern);
      }

      const response = await fetch(`${apiUrl}/api/search-heatmaps`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setHeatmapUrl(`${apiUrl}${result.heatmap}?ts=${Date.now()}`);
        setResults({
          ...results,
          heatmap: result.heatmap,
          summary:
            result.summary || {
              total_files: result.total_files || 0,
              hot_tier: result.hot_tier || 0,
              warm_tier: result.warm_tier || 0,
              cold_tier: result.cold_tier || 0,
            },
          search_info: {
            type: result.search_type,
            title: result.title,
            total_files: result.total_files,
            displayed_files: result.displayed_files,
            daily_reset: result.daily_reset,
          },
        });
      } else {
        const errorData = await response.json();
        setApiKeyWarning(errorData.detail || "Search failed");
      }
    } catch (error) {
      console.error("Search failed:", error);
      setApiKeyWarning("Search failed. Please try again.");
    } finally {
      setIsSearching(false);
    }
  };

  // Main analysis handler
  const handleRunAnalysis = async () => {
    if (!apiKey) {
      setApiKeyWarning("API Key is required to run analysis.");
      return;
    }
    if (!selectedLLM) {
      setApiKeyWarning("Please select an LLM provider.");
      return;
    }

    const formData = new FormData();
    formData.append("llm", selectedLLM);
    formData.append("api_key", apiKey);
    formData.append("top_n", topN.toString());

    const rawDir = selectedDirectory.trim();
    if (!rawDir) {
      setApiKeyWarning("Directory path cannot be empty.");
      return;
    }
    const monitorPath = rawDir.startsWith("/host-root")
      ? rawDir
      : `/host-root${rawDir.startsWith("/") ? rawDir : `/${rawDir}`}`;

    try {
      const configResponse = await fetch(`${apiUrl}/configure-monitoring`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ target_dir: monitorPath }),
      });
      if (!configResponse.ok) {
        const errBody = await configResponse.json();
        throw new Error(errBody.detail || "Unknown error configuring monitoring");
      }
    } catch (err) {
      setApiKeyWarning(err instanceof Error ? err.message : "Failed to configure monitoring.");
      return;
    }
    formData.append("directory", monitorPath);

    setApiKeyWarning("");
    setIsAnalyzing(true);

    try {
      const response = await fetch(`${apiUrl}/api/run-tiering`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errorMsg = errJson.detail;
        } catch {}
        setApiKeyWarning(errorMsg);
        return;
      }

      const result = await response.json();
      setResults(result);
      setHeatmapUrl(`${apiUrl}${result.heatmap}?ts=${Date.now()}`);
      if (result.summary) {
        setTotalFiles(result.summary.total_files);
      }
      setDailyResetInfo({
        isDailyReset: result.daily_reset,
        resetTime: result.reset_time,
        date: result.date,
        message: result.message,
      });
      fetchAvailableDates();
      setApiKeyWarning("");
    } catch (err) {
      setApiKeyWarning(err instanceof Error ? err.message : "Failed to run analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Manual reset handler
  const handleManualReset = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/manual-reset`, { method: "POST" });
      if (response.ok) {
        const result = await response.json();
        setResults(null);
        setHeatmapUrl("");
        setTotalFiles(null);
        setDailyResetInfo(null);
        setApiKeyWarning("");
        fetchAvailableDates();
        alert(`Manual reset completed: ${result.message}`);
      } else {
        const errorData = await response.json();
        setApiKeyWarning(errorData.message || "Manual reset failed");
      }
    } catch (error) {
      console.error("Manual reset failed:", error);
      setApiKeyWarning("Manual reset failed. Please try again.");
    }
  };

  // Export results as JSON
  const exportResults = () => {
    if (results) {
      const dataStr = JSON.stringify(results, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tiersense-analysis-${new Date().toISOString().split("T")[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  // Tier color helper
  const getTierColor = (tier: string) => {
    switch (tier) {
      case "HOT":
        return "bg-gradient-to-r from-red-500 to-red-600";
      case "WARM":
        return "bg-gradient-to-r from-amber-500 to-orange-500";
      case "COLD":
        return "bg-gradient-to-r from-blue-500 to-blue-600";
      default:
        return "bg-gradient-to-r from-gray-400 to-gray-500";
    }
  };

  // Clear only filters (not results)
  const clearSearch = () => {
    setSearchType("current");
    setSelectedDate("");
    setStartDate("");
    setEndDate("");
    setFilePattern("");
    setApiKeyWarning("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Fixed Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-xl border-b border-gray-200/60 shadow-lg">
        <div className="px-6 lg:px-8">
          <div className="flex justify-between items-center h-18">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                  <BarChart3 className="h-7 w-7 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                    TierSense
                  </h1>
                  <p className="text-xs text-gray-500 font-medium">Enterprise Storage Intelligence</p>
                </div>
              </div>
              {totalFiles !== null && (
                <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-full border border-blue-200 hover:bg-blue-100 transition-colors duration-200">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-semibold text-blue-700">{totalFiles.toLocaleString()} files</span>
                </div>
              )}
              {dailyResetInfo?.isDailyReset && (
                <div className="flex items-center space-x-2 bg-emerald-50 px-4 py-2 rounded-full border border-emerald-200 hover:bg-emerald-100 transition-colors duration-200">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-semibold text-emerald-700">Real-time Analytics</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleManualReset}
                variant="outline"
                size="sm"
                className="bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100 hover:border-orange-300 hover:shadow-md transition-all duration-200 font-medium"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reset System
              </Button>
              <Dialog open={showSettings} onOpenChange={setShowSettings}>
                <DialogTrigger asChild>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 hover:border-gray-300 hover:shadow-md transition-all duration-200 font-medium"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Configuration
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-lg">
                  <DialogHeader>
                    <DialogTitle className="flex items-center space-x-2 text-xl">
                      <Settings className="h-6 w-6 text-blue-600" />
                      <span>System Configuration</span>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-8">
                    <div>
                      <Label htmlFor="settings-api-key" className="text-sm font-semibold text-gray-700 mb-2 block">
                        API Authentication Key
                      </Label>
                      <div className="relative">
                        <Input
                          id="settings-api-key"
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="Enter your secure API key"
                          className="pr-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500 transition-colors duration-200"
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey((v) => !v)}
                          className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                          tabIndex={-1}
                        >
                          {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                      </div>
                    </div>

                    {/* Tier Ranges */}
                    <div className="pt-6 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-4 flex items-center space-x-2">
                        <TrendingUp className="h-4 w-4 text-blue-600" />
                        <span>Storage Tier Configuration</span>
                      </h4>
                      <div className="space-y-4">
                        {(["HOT", "WARM", "COLD"] as const).map((tier) => (
                          <div key={tier} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border">
                            <div className={`px-3 py-1.5 rounded-md text-xs font-bold text-white min-w-[60px] text-center ${
                              tier === "HOT" ? "bg-red-500" : tier === "WARM" ? "bg-amber-500" : "bg-blue-500"
                            }`}>
                              {tier}
                            </div>
                            <div className="flex items-center space-x-2 flex-1">
                              <Input
                                type="number"
                                min={0}
                                placeholder="min"
                                value={tierRanges[tier][0] ?? ""}
                                onChange={(e) => {
                                  const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                                  setTierRanges((prev) => ({ ...prev, [tier]: [v, prev[tier][1]] }));
                                }}
                                className="w-20 h-9 text-center"
                              />
                              <span className="text-gray-400 font-medium">to</span>
                              <Input
                                type="number"
                                min={0}
                                placeholder="max"
                                value={tierRanges[tier][1] ?? ""}
                                onChange={(e) => {
                                  const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                                  setTierRanges((prev) => ({ ...prev, [tier]: [prev[tier][0], v] }));
                                }}
                                className="w-20 h-9 text-center"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                      {tierError && <p className="text-sm text-red-600 mt-2 p-2 bg-red-50 rounded border border-red-200">{tierError}</p>}
                      <Button
                        className="w-full mt-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all duration-200 font-semibold"
                        onClick={async () => {
                          if (
                            tierRanges.HOT[0] !== null &&
                            tierRanges.WARM[1] !== null &&
                            tierRanges.HOT[0]! <= tierRanges.WARM[1]!
                          ) {
                            setTierError("HOT minimum must exceed WARM maximum");
                            return;
                          }
                          setTierError("");
                          const payload = {
                            api_key: apiKey,
                            default_llm: selectedLLM,
                            tier_ranges: tierRanges,
                          };
                          try {
                            const resp = await fetch(`${apiUrl}/api/settings`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify(payload),
                            });
                            if (resp.ok) setShowSettings(false);
                            else {
                              const err = await resp.json();
                              setTierError(err.detail || "Failed saving configuration");
                            }
                          } catch {
                            setTierError("Network error saving configuration");
                          }
                        }}
                      >
                        Save Configuration
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex h-screen pt-18">
        {/* Fixed Left Sidebar - Analysis Configuration (Wider with better spacing) */}
        <aside className="fixed left-0 w-96 h-full bg-white/90 backdrop-blur-xl border-r border-gray-200/60 shadow-xl overflow-y-auto">
          <div className="p-8">
            <div className="mb-8">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
                  <Zap className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">Analysis Setup</h2>
              </div>
              <div className="h-1.5 w-full bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-600 rounded-full shadow-sm"></div>
            </div>

            <div className="space-y-8">
              <div className="group">
                <Label htmlFor="llm-select" className="text-sm font-semibold text-gray-700 mb-3 block flex items-center space-x-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                  <span>AI Model Provider</span>
                </Label>
                <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                  <SelectTrigger className="border-gray-300 focus:border-blue-500 focus:ring-blue-500 hover:border-gray-400 transition-all duration-200 h-11">
                    <SelectValue placeholder="Choose AI Model" />
                  </SelectTrigger>
                  <SelectContent>
                    {llmOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="hover:bg-blue-50 transition-colors duration-150">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="group">
                <Label className="text-sm font-semibold text-gray-700 mb-3 block flex items-center space-x-2">
                  <Building2 className="h-4 w-4 text-blue-600" />
                  <span>Target Directory</span>
                </Label>
                <div className="space-y-4">
                  <Input
                    type="text"
                    placeholder="/host-root/mnt/enterprise-data"
                    value={selectedDirectory}
                    onChange={(e) => setSelectedDirectory(e.target.value)}
                    className="border-gray-300 focus:border-blue-500 focus:ring-blue-500 hover:border-gray-400 transition-all duration-200 h-11"
                  />
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-xs text-blue-700 font-medium">
                      <strong>Enterprise Tip:</strong> Use /host-root prefix for local paths (e.g., /host-root/data/production)
                    </p>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleRunAnalysis}
                disabled={!selectedLLM || isAnalyzing || !apiKey}
                className="w-full h-12 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:via-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl text-white font-semibold text-base"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Processing Analysis...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-3" />
                    Start AI Analysis
                  </>
                )}
              </Button>
              {apiKeyWarning && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg shadow-sm">
                  <p className="text-sm text-red-700 font-medium">{apiKeyWarning}</p>
                </div>
              )}

              {/* Enterprise Features Badge */}
              <div className="mt-8 p-4 bg-gradient-to-r from-emerald-50 to-blue-50 border border-emerald-200 rounded-xl">
                <h3 className="text-sm font-semibold text-emerald-700 mb-2 flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Enterprise Features</span>
                </h3>
                <ul className="text-xs text-emerald-600 space-y-1">
                  <li>• Real-time file access monitoring</li>
                  <li>• AI-powered tier recommendations</li>
                  <li>• Historical trend analysis</li>
                  <li>• Automated cost optimization</li>
                </ul>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area - Scrollable (Adjusted for wider sidebar) */}
        <main className="ml-96 flex-1 overflow-auto">
          <div className="p-8 pb-32">
            {results ? (
              <div className="space-y-8">
                {/* Daily Reset Banner */}
                {dailyResetInfo?.isDailyReset && (
                  <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 hover:shadow-lg transition-shadow duration-200">
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <Calendar className="h-6 w-6 text-blue-600 mr-4" />
                        <div>
                          <h3 className="text-base font-semibold text-blue-800">Real-time Analytics Active</h3>
                          <p className="text-sm text-blue-600 mt-1">
                            Access patterns refresh daily at {dailyResetInfo.resetTime} | Current session: {dailyResetInfo.date}
                          </p>
                          {dailyResetInfo.message && (
                            <p className="text-sm text-blue-600 mt-1 font-medium">{dailyResetInfo.message}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Summary Statistics */}
                <Card className="bg-white/90 backdrop-blur-sm border-gray-200/60 shadow-xl hover:shadow-2xl transition-shadow duration-300">
                  <CardHeader className="flex items-center justify-between pb-6">
                    <CardTitle className="text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                      {results.search_info?.title || "Enterprise Storage Analysis"}
                    </CardTitle>
                    <Button 
                      onClick={exportResults} 
                      variant="outline" 
                      size="sm"
                      className="bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100 hover:shadow-md transition-all duration-200 font-medium"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export Report
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-6">
                      <div className="text-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200 hover:shadow-lg transition-all duration-200 hover:scale-105">
                        <div className="text-3xl font-bold text-gray-900 mb-2">
                          {(results.summary?.total_files ?? results.search_info?.total_files ?? 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600 font-medium">Total Files</div>
                      </div>
                      <div className="text-center p-6 bg-gradient-to-br from-red-50 to-red-100 rounded-xl border border-red-200 hover:shadow-lg transition-all duration-200 hover:scale-105">
                        <div className="text-3xl font-bold text-red-600 mb-2">
                          {results.summary?.hot_tier ?? 0}
                        </div>
                        <div className="text-sm text-red-600 font-medium">HOT Tier</div>
                      </div>
                      <div className="text-center p-6 bg-gradient-to-br from-amber-50 to-orange-100 rounded-xl border border-amber-200 hover:shadow-lg transition-all duration-200 hover:scale-105">
                        <div className="text-3xl font-bold text-amber-600 mb-2">
                          {results.summary?.warm_tier ?? 0}
                        </div>
                        <div className="text-sm text-amber-600 font-medium">WARM Tier</div>
                      </div>
                      <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200 hover:shadow-lg transition-all duration-200 hover:scale-105">
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                          {results.summary?.cold_tier ?? 0}
                        </div>
                        <div className="text-sm text-blue-600 font-medium">COLD Tier</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Heatmap & Filters */}
                <Card className="bg-white/90 backdrop-blur-sm border-gray-200/60 shadow-xl hover:shadow-2xl transition-shadow duration-300">
                  <CardHeader>
                    <CardTitle className="flex items-center text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                      <BarChart3 className="h-6 w-6 mr-3 text-blue-600" />
                      Access Heatmap & Advanced Filters
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-8">
                    {/* Filter Controls */}
                    <div className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl p-6 border border-gray-200 shadow-sm">
                      <div className="flex items-center mb-4 space-x-2">
                        <Filter className="h-5 w-5 text-gray-600" />
                        <span className="text-base font-semibold text-gray-700">Visualization Controls</span>
                      </div>
                      <div className="flex flex-wrap items-end gap-6">
                        <div>
                          <Label className="text-xs font-medium text-gray-600 mb-2 block">Analysis Type</Label>
                          <Select value={searchType} onValueChange={setSearchType}>
                            <SelectTrigger className="h-10 w-36 border-gray-300 hover:border-gray-400 transition-colors duration-200">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="current">Real-time</SelectItem>
                              <SelectItem value="date">Historical Date</SelectItem>
                              <SelectItem value="range">Date Range</SelectItem>
                              <SelectItem value="pattern">File Pattern</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-gray-600 mb-2 block">Display Count</Label>
                          <Select value={topN.toString()} onValueChange={(v) => setTopN(+v)}>
                            <SelectTrigger className="h-10 w-28 border-gray-300 hover:border-gray-400 transition-colors duration-200">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="10">Top 10</SelectItem>
                              <SelectItem value="25">Top 25</SelectItem>
                              <SelectItem value="50">Top 50</SelectItem>
                              <SelectItem value="100">Top 100</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        {searchType === "date" && (
                          <div>
                            <Label className="text-xs font-medium text-gray-600 mb-2 block">Select Date</Label>
                            <Select value={selectedDate} onValueChange={setSelectedDate}>
                              <SelectTrigger className="h-10 w-40 border-gray-300 hover:border-gray-400 transition-colors duration-200">
                                <SelectValue placeholder="Choose date" />
                              </SelectTrigger>
                              <SelectContent>
                                {availableDates.map((date) => (
                                  <SelectItem key={date} value={date}>
                                    {date}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        )}
                        {searchType === "range" && (
                          <>
                            <div>
                              <Label className="text-xs font-medium text-gray-600 mb-2 block">Start Date</Label>
                              <Input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="h-10 w-40 border-gray-300 hover:border-gray-400 transition-colors duration-200"
                              />
                            </div>
                            <div>
                              <Label className="text-xs font-medium text-gray-600 mb-2 block">End Date</Label>
                              <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="h-10 w-40 border-gray-300 hover:border-gray-400 transition-colors duration-200"
                              />
                            </div>
                          </>
                        )}
                        {searchType === "pattern" && (
                          <div>
                            <Label className="text-xs font-medium text-gray-600 mb-2 block">File Pattern</Label>
                            <Input
                              placeholder="e.g., .log, report, *.txt"
                              value={filePattern}
                              onChange={(e) => setFilePattern(e.target.value)}
                              className="h-10 w-52 border-gray-300 hover:border-gray-400 transition-colors duration-200"
                            />
                          </div>
                        )}
                        <div className="flex ml-auto space-x-3">
                          <Button 
                            onClick={clearSearch} 
                            variant="outline" 
                            size="sm" 
                            className="h-10 bg-gray-50 border-gray-300 hover:bg-gray-100 transition-all duration-200"
                          >
                            Clear Filters
                          </Button>
                          <Button
                            onClick={handleAdvancedSearch}
                            disabled={isSearching}
                            size="sm"
                            className="h-10 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all duration-200 font-medium"
                          >
                            <Search className="h-4 w-4 mr-2" />
                            {isSearching ? "Searching..." : "Apply Filters"}
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Heatmap Display */}
                    <div className="text-center bg-white rounded-xl p-8 border border-gray-200 shadow-lg">
                      {heatmapUrl ? (
                        <img
                          src={heatmapUrl}
                          alt="Access Heatmap"
                          className="mx-auto rounded-lg border border-gray-300 max-w-full shadow-xl hover:shadow-2xl transition-shadow duration-300"
                          style={{ maxHeight: "600px", objectFit: "contain" }}
                          onError={(e) => {
                            console.error("Heatmap failed to load");
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="py-16 text-gray-500">
                          <BarChart3 className="mx-auto mb-6 h-20 w-20 opacity-30" />
                          <p className="text-xl font-semibold text-gray-700">Intelligence Visualization</p>
                          <p className="text-sm text-gray-500 mt-2">Run analysis to generate enterprise storage insights</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* File Analysis Results */}
                {results.analysis?.length > 0 && (
                  <Card className="bg-white/90 backdrop-blur-sm border-gray-200/60 shadow-xl hover:shadow-2xl transition-shadow duration-300">
                    <CardHeader>
                      <CardTitle className="text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                        AI Classification Results
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-5 border border-gray-200 rounded-xl bg-gradient-to-r from-white to-gray-50 hover:shadow-lg hover:border-gray-300 transition-all duration-200 group"
                          >
                            <div className="flex-1">
                              <div className="font-semibold text-sm text-gray-900 group-hover:text-blue-900 transition-colors duration-200">{file.path}</div>
                              <div className="text-xs text-gray-500 mt-1 flex items-center space-x-2">
                                <Activity className="h-3 w-3" />
                                <span>Access frequency: {file.access_frequency}</span>
                              </div>
                            </div>
                            <span
                              className={`px-4 py-2 text-xs font-bold text-white rounded-full shadow-sm hover:shadow-md transition-all duration-200 ${getTierColor(
                                file.tier
                              )}`}
                            >
                              {file.tier}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* JSON Output */}
                <Card className="bg-white/90 backdrop-blur-sm border-gray-200/60 shadow-xl hover:shadow-2xl transition-shadow duration-300">
                  <CardHeader>
                    <CardTitle className="flex items-center text-xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                      <FileText className="h-6 w-6 mr-3 text-blue-600" />
                      Raw Analysis Data
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      value={JSON.stringify(results, null, 2)}
                      readOnly
                      className="h-64 resize-none font-mono text-sm bg-gray-50 border-gray-300 hover:border-gray-400 transition-colors duration-200"
                    />
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-white/90 backdrop-blur-sm border-gray-200/60 shadow-xl h-96 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <BarChart3 className="mx-auto mb-8 h-20 w-20 opacity-30" />
                  <p className="text-2xl font-bold text-gray-700 mb-3">Ready for Enterprise Analysis</p>
                  <p className="text-sm text-gray-500 max-w-md mx-auto">
                    Configure your AI model and target directory in the analysis panel, then run intelligent storage tiering analysis
                  </p>
                </div>
              </Card>
            )}
          </div>
        </main>
      </div>

      {/* Professional Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-gray-900 via-slate-800 to-gray-900 text-white border-t border-gray-700 shadow-2xl z-40">
        <div className="px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-400" />
                <span className="font-semibold text-sm">TierSense Enterprise</span>
              </div>
              <div className="h-4 w-px bg-gray-600"></div>
              <p className="text-xs text-gray-300">© 2025 TierSense Analytics. Intelligent Storage Solutions.</p>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-4">
                <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors duration-200 hover:scale-110 transform">
                  <Github className="h-4 w-4" />
                </a>
                <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors duration-200 hover:scale-110 transform">
                  <Twitter className="h-4 w-4" />
                </a>
                <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors duration-200 hover:scale-110 transform">
                  <Linkedin className="h-4 w-4" />
                </a>
                <a href="#" className="text-gray-400 hover:text-blue-400 transition-colors duration-200 hover:scale-110 transform">
                  <Mail className="h-4 w-4" />
                </a>
              </div>
              <div className="h-4 w-px bg-gray-600"></div>
              <div className="text-xs text-gray-400 space-x-4">
                <a href="#" className="hover:text-blue-400 transition-colors duration-200">Enterprise Solutions</a>
                <a href="#" className="hover:text-blue-400 transition-colors duration-200">API Documentation</a>
                <a href="#" className="hover:text-blue-400 transition-colors duration-200">Support</a>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Enhanced Loading Overlay */}
      {(isAnalyzing || isSearching) && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-50">
          <div className="flex flex-col items-center p-10 bg-white rounded-2xl shadow-2xl border border-gray-200 max-w-md mx-4">
            <div className="h-16 w-16 mb-6 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600 shadow-lg"></div>
            <div className="text-xl font-bold text-gray-800 mb-2">
              {isAnalyzing ? "AI Processing In Progress" : "Searching Intelligence Database"}
            </div>
            <div className="text-sm text-gray-500 text-center">
              {isAnalyzing ? "Our AI is analyzing your storage patterns and generating tier recommendations..." : "Searching through historical data and generating visualizations..."}
            </div>
            <div className="mt-4 flex space-x-1">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
