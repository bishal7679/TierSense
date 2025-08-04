"use client";

import React, { useState, useEffect, useRef } from "react";
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
  Zap,
  Shield,
  Building2,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  GripVertical,
  Info,
  Clock,
  HardDrive,
  Sparkles,
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { llmOptions } from "@/src/config/llmOptions";

export default function TierSense() {
  // Sidebar state
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

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
    HOT: [100, 999],
    WARM: [20, 99],
    COLD: [0, 19],
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

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const minSidebarWidth = 280;
  const maxSidebarWidth = 600;

  // Sidebar resize functionality
  const startResize = (e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = e.clientX;
      if (newWidth >= minSidebarWidth && newWidth <= maxSidebarWidth) {
        setSidebarWidth(newWidth);
        setIsCollapsed(false);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Toggle collapse/expand
  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

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
          access_counts: result.access_counts, // Full access counts map
          top_items: result.top_items, // Top N items
          summary: result.summary || {
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
        return "bg-red-500 text-white";
      case "WARM":
        return "bg-orange-500 text-white";
      case "COLD":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-500 text-white";
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

  const effectiveSidebarWidth = isCollapsed ? 60 : sidebarWidth;

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Fixed Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-full mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-600 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-semibold text-gray-900">TierSense</h1>
                    <p className="text-sm text-gray-500">AI-Powered Storage Intelligence</p>
                  </div>
                </div>
                {dailyResetInfo?.isDailyReset && (
                  <div className="flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full border border-green-200">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-green-700">Live Analytics</span>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-3">
                <Button
                  onClick={handleManualReset}
                  variant="outline"
                  size="sm"
                  className="hover:bg-red-50 border-red-200 text-red-700 hover:text-red-800 hover:border-red-300"
                >
                  <RefreshCw className="h-4 w-4 mr-2 text-red-600" />
                  Reset
                </Button>
                <Dialog open={showSettings} onOpenChange={setShowSettings}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="hover:bg-gray-50">
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
                        <Label htmlFor="settings-api-key" className="text-sm font-medium text-gray-700 mb-2 block">
                          API Key
                        </Label>
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
                            className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600"
                            tabIndex={-1}
                          >
                            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      {/* Tier Ranges */}
                      <div className="pt-4 border-t border-gray-200">
                        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center space-x-2">
                          <HardDrive className="h-4 w-4" />
                          <span>Storage Tier Ranges (Access Counts)</span>
                        </h4>
                        {(["HOT", "WARM", "COLD"] as const).map((tier) => (
                          <div key={tier} className="flex items-center gap-3 mb-3">
                            <div className={`px-2 py-1 rounded text-xs font-medium text-white ${
                              tier === "HOT" ? "bg-red-500" : tier === "WARM" ? "bg-orange-500" : "bg-blue-500"
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
                          className="w-full mt-4 bg-blue-600 hover:bg-blue-700"
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
                          <Shield className="h-4 w-4 mr-2" />
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
        <div className="flex pt-20">
          {/* Resizable Left Sidebar */}
          <aside 
            ref={sidebarRef}
            className={`fixed left-0 top-20 h-screen bg-white border-r border-gray-200 overflow-hidden transition-all duration-200 ${
              isResizing ? 'select-none' : ''
            }`}
            style={{ width: `${effectiveSidebarWidth}px` }}
          >
            {/* Sidebar Content */}
            <div className="relative h-full">
              {/* Collapse/Expand Button */}
              <Button
                onClick={toggleSidebar}
                variant="ghost"
                size="sm"
                className="absolute top-4 right-2 z-10 h-8 w-8 p-0 hover:bg-gray-100"
              >
                {isCollapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>

              {/* Sidebar Main Content */}
              <div className={`h-full overflow-y-auto transition-opacity duration-200 ${
                isCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'
              }`}>
                <div className="p-6">
                  <div className="mb-6">
                    <div className="flex items-center space-x-2 mb-4">
                      <Sparkles className="h-5 w-5 text-blue-600" />
                      <h2 className="text-lg font-semibold text-gray-900">AI Analysis Setup</h2>
                    </div>
                    <div className="h-1 w-full bg-gradient-to-r from-blue-600 to-purple-600 rounded-full"></div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <Label htmlFor="llm-select" className="text-sm font-medium text-gray-700 mb-2 block flex items-center space-x-2">
                        <Zap className="h-4 w-4 text-blue-600" />
                        <span>AI Model Provider</span>
                      </Label>
                      <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                        <SelectTrigger>
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
                      <Label className="text-sm font-medium text-gray-700 mb-2 block flex items-center space-x-2">
                        <Building2 className="h-4 w-4 text-blue-600" />
                        <span>Target Directory</span>
                      </Label>
                      <Input
                        type="text"
                        placeholder="/host-root/mnt/data"
                        value={selectedDirectory}
                        onChange={(e) => setSelectedDirectory(e.target.value)}
                        className="font-mono text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-2 flex items-center space-x-1">
                        <Info className="h-3 w-3" />
                        <span>Use /host-root prefix for container paths</span>
                      </p>
                    </div>

                    <Button
                      onClick={handleRunAnalysis}
                      disabled={!selectedLLM || isAnalyzing || !apiKey}
                      className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isAnalyzing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Run AI Analysis
                        </>
                      )}
                    </Button>
                    {apiKeyWarning && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-xs text-red-600 flex items-start space-x-2">
                          <Shield className="h-3 w-3 mt-0.5 flex-shrink-0" />
                          <span>{apiKeyWarning}</span>
                        </p>
                      </div>
                    )}

                    {/* Enterprise Features */}
                    <div className="mt-6 p-4 bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
                      <h3 className="text-sm font-semibold text-blue-900 mb-2 flex items-center space-x-2">
                        <TrendingUp className="h-4 w-4" />
                        <span>Enterprise Features</span>
                      </h3>
                      <ul className="text-xs text-blue-700 space-y-1">
                        <li>• Real-time file access monitoring</li>
                        <li>• AI-powered tier recommendations</li>
                        <li>• Context-aware storage suggestions</li>
                        <li>• Dynamic filesystem metadata</li>
                        <li>• Historical trend analysis</li>
                        <li>• Cost optimization insights</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Collapsed State Icon */}
              {isCollapsed && (
                <div className="flex flex-col items-center justify-center h-full space-y-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Sparkles className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="writing-mode-vertical text-sm font-medium text-gray-600 transform rotate-180">
                    AI Analysis
                  </div>
                </div>
              )}
            </div>

            {/* Resize Handle */}
            {!isCollapsed && (
              <div
                className="absolute top-0 right-0 w-1 h-full bg-gray-300 opacity-0 hover:opacity-100 cursor-col-resize transition-opacity duration-200 group"
                onMouseDown={startResize}
              >
                <div className="absolute top-1/2 right-0 transform translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <GripVertical className="h-4 w-4 text-gray-500" />
                </div>
              </div>
            )}
          </aside>

          {/* Main Content Area */}
          <main 
            className="flex-1 p-6 transition-all duration-200"
            style={{ marginLeft: `${effectiveSidebarWidth}px` }}
          >
            {results ? (
              <div className="space-y-6">
                {/* Daily Reset Banner */}
                {dailyResetInfo?.isDailyReset && (
                  <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
                    <CardContent className="p-4">
                      <div className="flex items-center">
                        <Calendar className="h-5 w-5 text-green-600 mr-3" />
                        <div>
                          <h3 className="text-sm font-medium text-green-800 flex items-center space-x-2">
                            <span>Real-time Analytics Active</span>
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          </h3>
                          <p className="text-xs text-green-600 mt-1">
                            Access patterns refresh daily at {dailyResetInfo.resetTime} | Current session: {dailyResetInfo.date}
                          </p>
                          {dailyResetInfo.message && (
                            <p className="text-xs text-green-600 mt-1 flex items-center space-x-1">
                              <Clock className="h-3 w-3" />
                              <span>{dailyResetInfo.message}</span>
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Summary Statistics */}
                <Card>
                  <CardHeader className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                      <BarChart3 className="h-5 w-5 text-blue-600" />
                      <span>{results.search_info?.title || "Storage Analysis Summary"}</span>
                    </CardTitle>
                    <Button onClick={exportResults} variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export Data
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-gray-50 rounded-lg border">
                        <div className="text-2xl font-bold text-gray-900">
                          {(results.summary?.total_files ?? results.search_info?.total_files ?? 0).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-600 mt-1 flex items-center justify-center space-x-1">
                          <FileText className="h-3 w-3" />
                          <span>Total Files</span>
                        </div>
                      </div>
                      <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
                        <div className="text-2xl font-bold text-red-600">
                          {results.summary?.hot_tier ?? 0}
                        </div>
                        <div className="text-sm text-red-600 mt-1 font-medium">HOT</div>
                      </div>
                      <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <div className="text-2xl font-bold text-orange-600">
                          {results.summary?.warm_tier ?? 0}
                        </div>
                        <div className="text-sm text-orange-600 mt-1 font-medium">WARM</div>
                      </div>
                      <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="text-2xl font-bold text-blue-600">
                          {results.summary?.cold_tier ?? 0}
                        </div>
                        <div className="text-sm text-blue-600 mt-1 font-medium">COLD</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Heatmap & Filters */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-semibold text-gray-900">
                      <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                      Access Heatmap & Filters
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Filter Controls */}
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-center mb-3 space-x-2">
                        <Filter className="h-4 w-4 text-gray-600" />
                        <span className="text-sm font-medium text-gray-700">Visualization Controls</span>
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
                          <Label className="text-xs text-gray-600">Display Count</Label>
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
                            className="h-8 bg-blue-600 hover:bg-blue-700"
                          >
                            <Search className="h-3 w-3 mr-1" />
                            {isSearching ? (
                              <>
                                <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent mr-1"></div>
                                Searching...
                              </>
                            ) : (
                              "Apply"
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Heatmap Display */}
                    <div className="text-center bg-white rounded-lg p-6 border border-gray-200">
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

                {/* Enhanced File Analysis Results */}
                {results.analysis?.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                        <Sparkles className="h-5 w-5 text-blue-600" />
                        <span>AI-Powered Classification Results</span>
                        <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                          Enhanced with Context
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors duration-200"
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex-1">
                                <div className="font-medium text-sm text-gray-900 font-mono">
                                  {file.path}
                                </div>
                                <div className="text-xs text-gray-500 mt-1 flex items-center space-x-4">
                                  <span className="flex items-center space-x-1">
                                    <BarChart3 className="h-3 w-3" />
                                    <span>Access: {file.access_frequency}</span>
                                  </span>
                                  {file.metadata?.size_mb && (
                                    <span className="flex items-center space-x-1">
                                      <HardDrive className="h-3 w-3" />
                                      <span>Size: {file.metadata.size_mb}MB</span>
                                    </span>
                                  )}
                                  {file.metadata?.modified && (
                                    <span className="flex items-center space-x-1">
                                      <Clock className="h-3 w-3" />
                                      <span>Modified: {file.metadata.modified}</span>
                                    </span>
                                  )}
                                </div>
                              </div>
                              <span
                                className={`px-3 py-1.5 text-xs font-semibold rounded-full ${getTierColor(file.tier)}`}
                              >
                                {file.tier}
                              </span>
                            </div>
                            
                            {/* AI Suggestion */}
                            {file.suggestion && (
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                                <div className="flex items-start space-x-2">
                                  <Sparkles className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                  <div>
                                    <p className="text-xs font-medium text-blue-800 mb-1">AI Recommendation</p>
                                    <p className="text-xs text-blue-700">{file.suggestion}</p>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* JSON Output */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg font-semibold text-gray-900">
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
              <Card className="h-96 flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
                <div className="text-center text-gray-500">
                  <div className="relative">
                    <BarChart3 className="mx-auto mb-6 h-16 w-16 opacity-30" />
                    <Sparkles className="absolute -top-2 -right-2 h-6 w-6 text-blue-600 opacity-60" />
                  </div>
                  <p className="text-xl font-medium text-gray-700">Ready for AI Analysis</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Configure your settings in the left panel and run analysis to see intelligent tiering results
                  </p>
                  <p className="text-xs text-blue-600 mt-4 flex items-center justify-center space-x-1">
                    <Info className="h-3 w-3" />
                    <span>Enhanced with context-aware suggestions and metadata</span>
                  </p>
                </div>
              </Card>
            )}
          </main>
        </div>

        {/* Enhanced Loading Overlay */}
        {(isAnalyzing || isSearching) && (
          <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
            <div className="bg-white rounded-xl shadow-2xl p-8 flex flex-col items-center space-y-4 border border-gray-200">
              <div className="relative">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                <Sparkles className="absolute inset-0 m-auto h-6 w-6 text-blue-600 animate-pulse" />
              </div>
              <div className="text-lg font-medium text-gray-800">
                {isAnalyzing ? "AI Analysis in Progress..." : "Searching..."}
              </div>
              <div className="text-sm text-gray-500 text-center">
                {isAnalyzing 
                  ? "Processing your data with intelligent recommendations" 
                  : "Finding results with enhanced filtering"
                }
              </div>
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}