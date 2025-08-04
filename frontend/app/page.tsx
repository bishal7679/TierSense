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
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
        <div className="px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                    TierSense
                  </h1>
                  <p className="text-xs text-gray-500">AI-Powered Storage Analytics</p>
                </div>
              </div>
              {totalFiles !== null && (
                <div className="flex items-center space-x-2 bg-blue-50 px-3 py-1.5 rounded-full">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-700">{totalFiles} files</span>
                </div>
              )}
              {dailyResetInfo?.isDailyReset && (
                <div className="flex items-center space-x-2 bg-green-50 px-3 py-1.5 rounded-full">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-700">Daily Reset Active</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleManualReset}
                variant="outline"
                size="sm"
                className="bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100 hover:border-orange-300 transition-all duration-200"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reset
              </Button>
              <Dialog open={showSettings} onOpenChange={setShowSettings}>
                <DialogTrigger asChild>
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 hover:border-gray-300 transition-all duration-200"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle className="flex items-center space-x-2">
                      <Settings className="h-5 w-5 text-blue-600" />
                      <span>Configuration</span>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-6">
                    <div>
                      <Label htmlFor="settings-api-key" className="text-sm font-medium text-gray-700">
                        API Key
                      </Label>
                      <div className="relative mt-1">
                        <Input
                          id="settings-api-key"
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="Enter your API key"
                          className="pr-10 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey((v) => !v)}
                          className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600"
                          tabIndex={-1}
                        >
                          {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Tier Ranges */}
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Storage Tier Ranges</h4>
                      {(["HOT", "WARM", "COLD"] as const).map((tier) => (
                        <div key={tier} className="flex items-center gap-3 mb-3">
                          <div className={`px-2 py-1 rounded text-xs font-medium text-white ${
                            tier === "HOT" ? "bg-red-500" : tier === "WARM" ? "bg-amber-500" : "bg-blue-500"
                          }`}>
                            {tier}
                          </div>
                          <Input
                            type="number"
                            min={0}
                            placeholder="min"
                            value={tierRanges[tier][0] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                              setTierRanges((prev) => ({ ...prev, [tier]: [v, prev[tier][1]] }));
                            }}
                            className="w-20 h-8"
                          />
                          <span className="text-gray-400">—</span>
                          <Input
                            type="number"
                            min={0}
                            placeholder="max"
                            value={tierRanges[tier][1] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                              setTierRanges((prev) => ({ ...prev, [tier]: [prev[tier][0], v] }));
                            }}
                            className="w-20 h-8"
                          />
                        </div>
                      ))}
                      {tierError && <p className="text-xs text-red-600 mt-1">{tierError}</p>}
                      <Button
                        className="w-full mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                        onClick={async () => {
                          if (
                            tierRanges.HOT[0] !== null &&
                            tierRanges.WARM[1] !== null &&
                            tierRanges.HOT[0]! <= tierRanges.WARM[1]!
                          ) {
                            setTierError("HOT min must exceed WARM max");
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
                              setTierError(err.detail || "Failed saving settings");
                            }
                          } catch {
                            setTierError("Network error saving settings");
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
      <div className="flex h-screen pt-16">
        {/* Fixed Left Sidebar - Analysis Configuration */}
        <aside className="fixed left-0 w-80 h-full bg-white/80 backdrop-blur-xl border-r border-gray-200/50 shadow-sm overflow-y-auto">
          <div className="p-6">
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-4">
                <Zap className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">Analysis Setup</h2>
              </div>
              <div className="h-1 w-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"></div>
            </div>

            <div className="space-y-6">
              <div>
                <Label htmlFor="llm-select" className="text-sm font-medium text-gray-700 mb-2 block">
                  AI Model Provider
                </Label>
                <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                  <SelectTrigger className="border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Choose AI Model" />
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
                <Label className="text-sm font-medium text-gray-700 mb-3 block">
                  Target Directory
                </Label>
                <div className="space-y-3">
                  <Input
                    type="text"
                    placeholder="/host-root/mnt/data"
                    value={selectedDirectory}
                    onChange={(e) => setSelectedDirectory(e.target.value)}
                    className="border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500">
                    Use /host-root prefix for local paths (e.g., /host-root/home/user/docs)
                  </p>
                </div>
              </div>

              <Button
                onClick={handleRunAnalysis}
                disabled={!selectedLLM || isAnalyzing || !apiKey}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
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
              {apiKeyWarning && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-xs text-red-600">{apiKeyWarning}</p>
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content Area - Scrollable */}
        <main className="ml-80 flex-1 overflow-auto">
          <div className="p-6">
            {results ? (
              <div className="space-y-6">
                {/* Daily Reset Banner */}
                {dailyResetInfo?.isDailyReset && (
                  <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                    <CardContent className="p-4">
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 text-blue-600 mr-3" />
                        <div>
                          <h3 className="text-sm font-medium text-blue-800">Daily Reset Active</h3>
                          <p className="text-xs text-blue-600 mt-1">
                            Access counts reset daily at {dailyResetInfo.resetTime} | Current date:{" "}
                            {dailyResetInfo.date}
                          </p>
                          {dailyResetInfo.message && (
                            <p className="text-xs text-blue-600 mt-1">{dailyResetInfo.message}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Summary Statistics */}
                <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg">
                  <CardHeader className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      {results.search_info?.title || "Analysis Summary"}
                    </CardTitle>
                    <Button 
                      onClick={exportResults} 
                      variant="outline" 
                      size="sm"
                      className="bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl">
                        <div className="text-2xl font-bold text-gray-900">
                          {results.summary?.total_files ?? results.search_info?.total_files ?? 0}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">Total Files</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl">
                        <div className="text-2xl font-bold text-red-600">
                          {results.summary?.hot_tier ?? 0}
                        </div>
                        <div className="text-sm text-red-600 mt-1">HOT</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-amber-50 to-orange-100 rounded-xl">
                        <div className="text-2xl font-bold text-amber-600">
                          {results.summary?.warm_tier ?? 0}
                        </div>
                        <div className="text-sm text-amber-600 mt-1">WARM</div>
                      </div>
                      <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                        <div className="text-2xl font-bold text-blue-600">
                          {results.summary?.cold_tier ?? 0}
                        </div>
                        <div className="text-sm text-blue-600 mt-1">COLD</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Heatmap & Filters */}
                <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                      Access Heatmap & Filters
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Filter Controls */}
                    <div className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl p-4 border border-gray-200">
                      <div className="flex items-center mb-3 space-x-2">
                        <Filter className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Visualization Filters</span>
                      </div>
                      <div className="flex flex-wrap items-end gap-4">
                        <div>
                          <Label className="text-xs text-gray-600">Search Type</Label>
                          <Select value={searchType} onValueChange={setSearchType}>
                            <SelectTrigger className="h-8 w-32 border-gray-300">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="current">Current Day</SelectItem>
                              <SelectItem value="date">Specific Date</SelectItem>
                              <SelectItem value="range">Date Range</SelectItem>
                              <SelectItem value="pattern">File Pattern</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-600">Display Count</Label>
                          <Select value={topN.toString()} onValueChange={(v) => setTopN(+v)}>
                            <SelectTrigger className="h-8 w-24 border-gray-300">
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
                            <Label className="text-xs text-gray-600">Select Date</Label>
                            <Select value={selectedDate} onValueChange={setSelectedDate}>
                              <SelectTrigger className="h-8 w-32 border-gray-300">
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
                              <Label className="text-xs text-gray-600">Start Date</Label>
                              <Input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="h-8 w-36 border-gray-300"
                              />
                            </div>
                            <div>
                              <Label className="text-xs text-gray-600">End Date</Label>
                              <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="h-8 w-36 border-gray-300"
                              />
                            </div>
                          </>
                        )}
                        {searchType === "pattern" && (
                          <div>
                            <Label className="text-xs text-gray-600">File Pattern</Label>
                            <Input
                              placeholder="e.g., .log, report"
                              value={filePattern}
                              onChange={(e) => setFilePattern(e.target.value)}
                              className="h-8 w-48 border-gray-300"
                            />
                          </div>
                        )}
                        <div className="flex ml-auto space-x-2">
                          <Button 
                            onClick={clearSearch} 
                            variant="outline" 
                            size="sm" 
                            className="h-8 bg-gray-50 border-gray-300"
                          >
                            Clear
                          </Button>
                          <Button
                            onClick={handleAdvancedSearch}
                            disabled={isSearching}
                            size="sm"
                            className="h-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                          >
                            <Search className="h-3 w-3 mr-1" />
                            {isSearching ? "Searching..." : "Apply"}
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Heatmap Display */}
                    <div className="text-center bg-white rounded-xl p-6 border border-gray-200">
                      {heatmapUrl ? (
                        <img
                          src={heatmapUrl}
                          alt="Access Heatmap"
                          className="mx-auto rounded-lg border border-gray-300 max-w-full shadow-lg"
                          style={{ maxHeight: "600px", objectFit: "contain" }}
                          onError={(e) => {
                            console.error("Heatmap failed to load");
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="py-12 text-gray-500">
                          <BarChart3 className="mx-auto mb-4 h-16 w-16 opacity-30" />
                          <p className="text-lg font-medium">Visualization will appear here</p>
                          <p className="text-sm">Run analysis to generate the access heatmap</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* File Analysis Results */}
                {results.analysis?.length > 0 && (
                  <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                        File Classification Results
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-4 border border-gray-200 rounded-xl bg-gradient-to-r from-white to-gray-50 hover:shadow-md transition-shadow duration-200"
                          >
                            <div>
                              <div className="font-medium text-sm text-gray-900">{file.path}</div>
                              <div className="text-xs text-gray-500 mt-1">
                                Access frequency: {file.access_frequency}
                              </div>
                            </div>
                            <span
                              className={`px-3 py-1.5 text-xs font-semibold text-white rounded-full ${getTierColor(
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
                <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      <FileText className="h-5 w-5 mr-2 text-blue-600" />
                      Raw JSON Output
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      value={JSON.stringify(results, null, 2)}
                      readOnly
                      className="h-64 resize-none font-mono text-sm bg-gray-50 border-gray-300"
                    />
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg h-96 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <BarChart3 className="mx-auto mb-6 h-16 w-16 opacity-30" />
                  <p className="text-xl font-medium text-gray-700">Ready for Analysis</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Configure your settings in the left panel and run analysis to see intelligent tiering results
                  </p>
                </div>
              </Card>
            )}
          </div>
        </main>
      </div>

      {/* Loading Overlay */}
      {(isAnalyzing || isSearching) && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-50">
          <div className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-2xl">
            <div className="h-12 w-12 mb-4 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
            <div className="text-lg font-semibold text-gray-800">
              {isAnalyzing ? "Analyzing your data with AI..." : "Searching heatmaps..."}
            </div>
            <div className="mt-2 text-sm text-gray-500">This may take a few moments</div>
          </div>
        </div>
      )}
    </div>
  );
}