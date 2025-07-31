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
  const [inputSource, setInputSource] = useState("default");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
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

    if (inputSource === "upload") {
      if (!uploadedFile) {
        setApiKeyWarning("Please select and upload a valid .ndjson file.");
        return;
      }
      formData.append("file", uploadedFile);
    } else {
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
    }

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

  // File upload handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith(".ndjson")) {
      setUploadedFile(file);
      setApiKeyWarning("");
    } else if (file) {
      setApiKeyWarning("Please select a valid .ndjson file.");
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
        return "bg-red-500";
      case "WARM":
        return "bg-yellow-500";
      case "COLD":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-8 w-8 text-slate-700" />
              <h1 className="text-2xl font-semibold text-slate-900">TierSense</h1>
              {totalFiles !== null && (
                <span className="ml-2 text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                  {totalFiles} files
                </span>
              )}
              {dailyResetInfo?.isDailyReset && (
                <div className="flex items-center space-x-2">
                  <span
                    className="w-3 h-3 bg-green-400 rounded-full animate-pulse"
                    style={{ boxShadow: "0 0 6px 2px rgba(34,197,94,0.7)" }}
                  />
                  <span className="text-green-600 font-medium">Daily Reset Active</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleManualReset}
                variant="outline"
                size="sm"
                className="text-orange-600 border-orange-300 hover:bg-orange-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Manual Reset
              </Button>
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
                      <div className="relative">
                        <Input
                          id="settings-api-key"
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="Enter your API key"
                          className="pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey((v) => !v)}
                          className="absolute inset-y-0 right-0 flex items-center px-2 text-slate-500"
                          tabIndex={-1}
                        >
                          {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                      </div>
                    </div>

                    {/* Tier Ranges */}
                    <div className="mt-4 pt-4 border-t">
                      <DialogTitle className="text-base">Tier Ranges</DialogTitle>
                      {(["HOT", "WARM", "COLD"] as const).map((tier) => (
                        <div key={tier} className="flex items-center gap-2 mt-2">
                          <Label className="w-12">{tier}</Label>
                          <Input
                            type="number"
                            min={0}
                            placeholder="min"
                            value={tierRanges[tier][0] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                              setTierRanges((prev) => ({ ...prev, [tier]: [v, prev[tier][1]] }));
                            }}
                            className="w-20"
                          />
                          <span>-</span>
                          <Input
                            type="number"
                            min={0}
                            placeholder="max"
                            value={tierRanges[tier][1] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                              setTierRanges((prev) => ({ ...prev, [tier]: [prev[tier][0], v] }));
                            }}
                            className="w-20"
                          />
                        </div>
                      ))}
                      {tierError && <p className="text-xs text-red-600 mt-1">{tierError}</p>}
                      <Button
                        variant="secondary"
                        className="w-full mt-3"
                        onClick={async () => {
                          // Simple validation example
                          if (
                            tierRanges.HOT[0] !== null &&
                            tierRanges.WARM[1] !== null &&
                            tierRanges.HOT[0]! <= tierRanges.WARM[1]!
                          ) {
                            setTierError("HOT min must exceed WARM max");
                            return;
                          }
                          setTierError("");
                          // Save settings & tierRanges
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
                        Save Configuration & Tier Ranges
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Analysis Config */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">Analysis Configuration</CardTitle>
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
                      <Label htmlFor="default-logs" className="text-sm font-normal">
                        Use default /logs folder
                      </Label>
                    </div>
                    {inputSource === "default" && (
                      <div className="mt-2">
                        <Label htmlFor="selectedDirectory" className="text-sm">
                          Directory Path
                        </Label>
                        <Input
                          id="selectedDirectory"
                          type="text"
                          placeholder="/host-root/mnt/data"
                          value={selectedDirectory}
                          onChange={(e) => setSelectedDirectory(e.target.value)}
                          className="mt-1"
                        />
                        <p className="text-xs text-slate-500 mt-1">
                          Prefix local paths with /host-root/ (e.g., /host-root/home/user/docs).
                        </p>
                      </div>
                    )}
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
                      <Label htmlFor="upload-file" className="text-sm font-normal">
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
                        <p className="mt-2 text-sm text-slate-600">Selected: {uploadedFile.name}</p>
                      )}
                    </div>
                  </div>
                )}
                <Button
                  onClick={handleRunAnalysis}
                  disabled={!selectedLLM || isAnalyzing || !apiKey}
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
                {apiKeyWarning && <p className="text-xs text-red-600 mt-1">{apiKeyWarning}</p>}
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {results ? (
              <div className="space-y-6">
                {/* Daily Reset Banner */}
                {dailyResetInfo?.isDailyReset && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
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
                  </div>
                )}

                {/* Summary */}
                <Card>
                  <CardHeader className="flex items-center justify-between">
                    <CardTitle className="text-lg font-medium">
                      {results.search_info?.title || "Analysis Summary"}
                    </CardTitle>
                    <Button onClick={exportResults} variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-semibold text-slate-900">
                          {results.summary?.total_files ?? results.search_info?.total_files ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">Total Files</div>
                      </div>
                      <div>
                        <div className="text-2xl font-semibold text-red-600">
                          {results.summary?.hot_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">HOT</div>
                      </div>
                      <div>
                        <div className="text-2xl font-semibold text-yellow-600">
                          {results.summary?.warm_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">WARM</div>
                      </div>
                      <div>
                        <div className="text-2xl font-semibold text-blue-600">
                          {results.summary?.cold_tier ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">COLD</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Heatmap & Filters */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-medium">
                      <BarChart3 className="h-5 w-5 mr-2" />
                      Access Heatmap & Filters
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                      <div className="flex items-center mb-3 space-x-2">
                        <Filter className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Heatmap Filters</span>
                      </div>
                      <div className="flex flex-wrap items-end gap-4">
                        <div>
                          <Label className="text-xs text-gray-600">Search Type</Label>
                          <Select value={searchType} onValueChange={setSearchType}>
                            <SelectTrigger className="h-8 w-32">
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
                          <Label className="text-xs text-gray-600">Show Files</Label>
                          <Select value={topN.toString()} onValueChange={(v) => setTopN(+v)}>
                            <SelectTrigger className="h-8 w-24">
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
                              <SelectTrigger className="h-8 w-32">
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
                                className="h-8 w-36"
                              />
                            </div>
                            <div>
                              <Label className="text-xs text-gray-600">End Date</Label>
                              <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="h-8 w-36"
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
                              className="h-8 w-48"
                            />
                          </div>
                        )}
                        <div className="flex ml-auto space-x-2">
                          <Button onClick={clearSearch} variant="outline" size="sm" className="h-8">
                            Clear
                          </Button>
                          <Button
                            onClick={handleAdvancedSearch}
                            disabled={isSearching}
                            size="sm"
                            className="h-8 flex items-center"
                          >
                            <Search className="h-3 w-3 mr-1" />
                            {isSearching ? "Searching..." : "Apply"}
                          </Button>
                        </div>
                      </div>
                    </div>
                    <div className="text-center">
                      {heatmapUrl ? (
                        <img
                          src={heatmapUrl}
                          alt="Access Heatmap"
                          className="mx-auto rounded border border-gray-300 max-w-full"
                          style={{ maxHeight: "600px", objectFit: "contain" }}
                          onError={(e) => {
                            console.error("Heatmap failed to load");
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="py-8 text-slate-500">
                          <BarChart3 className="mx-auto mb-4 h-12 w-12 opacity-50" />
                          <p>Heatmap will appear here after analysis</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* File Analysis Section */}
                {results.analysis?.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg font-medium">File Analysis Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 border rounded-lg"
                          >
                            <div>
                              <div className="font-medium text-sm">{file.path}</div>
                              <div className="text-xs text-slate-500">
                                Access frequency: {file.access_frequency}
                              </div>
                            </div>
                            <span
                              className={`px-2 py-1 text-xs text-white rounded ${getTierColor(
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
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-medium">
                      <FileText className="h-5 w-5 mr-2" />
                      JSON Output
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      value={JSON.stringify(results, null, 2)}
                      readOnly
                      className="h-64 resize-none font-mono text-sm"
                    />
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="flex items-center justify-center h-96">
                <div className="text-center text-slate-500">
                  <BarChart3 className="mx-auto mb-4 h-12 w-12 opacity-50" />
                  <p className="text-lg font-medium">No Analysis Results</p>
                  <p className="text-sm">Configure your settings and run an analysis to see results</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>

      {/* Loading Overlay */}
      {(isAnalyzing || isSearching) && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
          <div className="flex flex-col items-center p-8 bg-white rounded-lg shadow-lg">
            <div className="h-12 w-12 mb-4 animate-spin rounded-full border-b-4 border-blue-600"></div>
            <div className="text-lg font-medium text-slate-800">
              {isAnalyzing ? "TierSense is analyzing your data..." : "Searching heatmaps..."}
            </div>
            <div className="mt-2 text-sm text-slate-500">This may take a few moments</div>
          </div>
        </div>
      )}
    </div>
  );
}
