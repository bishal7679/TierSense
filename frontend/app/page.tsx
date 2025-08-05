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
  Building2,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  GripVertical,
  Folder,
  FolderOpen,
  HardDrive,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Grid3X3,
  List,
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

// Common directory suggestions for easier selection - REMOVED Custom Path
const commonDirectories = [
  { label: "Data Directory", value: "/host-root/mnt/data", icon: <HardDrive className="h-4 w-4" /> },
  { label: "NFS Mount", value: "/host-root/mnt/nfs", icon: <Folder className="h-4 w-4" /> },
  { label: "Home Directory", value: "/host-root/home", icon: <FolderOpen className="h-4 w-4" /> },
  { label: "Var Logs", value: "/host-root/var/log", icon: <FileText className="h-4 w-4" /> },
  { label: "Optional Apps", value: "/host-root/opt", icon: <Building2 className="h-4 w-4" /> },
];

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
  const [selectedDirectoryType, setSelectedDirectoryType] = useState("");

  // Heatmap zoom state - DEFAULT TO 50%
  const [heatmapZoom, setHeatmapZoom] = useState(50);
  const [heatmapPosition, setHeatmapPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const heatmapContainerRef = useRef<HTMLDivElement>(null);

  // AI suggestions view state
  const [suggestionsViewMode, setSuggestionsViewMode] = useState<'grid' | 'list'>('grid');

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

  // Heatmap zoom functions
  const handleZoomIn = () => {
    setHeatmapZoom(prev => Math.min(prev + 25, 300));
  };

  const handleZoomOut = () => {
    setHeatmapZoom(prev => Math.max(prev - 25, 50));
  };

  // Reset to DEFAULT 50%
  const resetHeatmapView = () => {
    setHeatmapZoom(50);
    setHeatmapPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (heatmapZoom > 100) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - heatmapPosition.x,
        y: e.clientY - heatmapPosition.y
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && heatmapZoom > 100) {
      setHeatmapPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

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
    const savedDir = localStorage.getItem("tiersense_selected_directory");
    if (savedDir) setSelectedDirectory(savedDir);
    const savedDirType = localStorage.getItem("tiersense_selected_directory_type");
    if (savedDirType) setSelectedDirectoryType(savedDirType);
    fetchAvailableDates();
  }, []);

  // Persist API key and directory selections
  useEffect(() => {
    if (apiKey) localStorage.setItem("tiersense_api_key", apiKey);
  }, [apiKey]);

  useEffect(() => {
    if (selectedDirectory) localStorage.setItem("tiersense_selected_directory", selectedDirectory);
  }, [selectedDirectory]);

  useEffect(() => {
    if (selectedDirectoryType) localStorage.setItem("tiersense_selected_directory_type", selectedDirectoryType);
  }, [selectedDirectoryType]);

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

  // Handle directory type selection - UPDATED TO REMOVE CUSTOM LOGIC
  const handleDirectoryTypeChange = (value: string) => {
    setSelectedDirectoryType(value);
    const selectedDir = commonDirectories.find(dir => dir.value === value);
    if (selectedDir) {
      setSelectedDirectory(selectedDir.value);
    }
  };

  // Normalize directory path to ensure proper /host-root prefix
  const normalizeDirectoryPath = (path: string): string => {
    if (!path) return "";
    
    const trimmedPath = path.trim();
    
    // If already starts with /host-root, return as is
    if (trimmedPath.startsWith("/host-root")) {
      return trimmedPath;
    }
    
    // If starts with /, prepend /host-root
    if (trimmedPath.startsWith("/")) {
      return `/host-root${trimmedPath}`;
    }
    
    // Otherwise, add /host-root/ prefix
    return `/host-root/${trimmedPath}`;
  };

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

  // Enhanced audit rule configuration helper
  const ensureAuditRule = async (targetDir: string) => {
    const normalizedPath = normalizeDirectoryPath(targetDir);
    
    const formData = new FormData();
    formData.append('target_dir', normalizedPath);
    
    const response = await fetch(`${apiUrl}/configure-monitoring`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ target_dir: normalizedPath }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || response.statusText);
    }
    
    return response.json();
  };

  // Advanced search handler with improved directory support
  const handleAdvancedSearch = async () => {
    setIsSearching(true);
    setApiKeyWarning("");

    try {
      const formData = new FormData();
      formData.append("search_type", searchType);
      formData.append("top_n", topN.toString());

      if (selectedDirectory) {
        const normalizedPath = normalizeDirectoryPath(selectedDirectory);
        formData.append("directory", normalizedPath);
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
            directory: normalizeDirectoryPath(selectedDirectory),
          },
        });
        // Reset zoom when new heatmap loads
        resetHeatmapView();
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

  // Enhanced main analysis handler with audit rule configuration
  const handleRunAnalysis = async () => {
    if (!apiKey) {
      setApiKeyWarning("API Key is required to run analysis.");
      return;
    }
    if (!selectedLLM) {
      setApiKeyWarning("Please select an LLM provider.");
      return;
    }

    const rawDir = selectedDirectory.trim();
    if (!rawDir) {
      setApiKeyWarning("Directory path cannot be empty.");
      return;
    }

    const normalizedPath = normalizeDirectoryPath(rawDir);

    setApiKeyWarning("");
    setIsAnalyzing(true);

    try {
      // 1. Configure audit rule for the target directory
      await ensureAuditRule(normalizedPath);
      
      // 2. Run the tiering analysis
      const formData = new FormData();
      formData.append("llm", selectedLLM);
      formData.append("api_key", apiKey);
      formData.append("directory", normalizedPath);
      formData.append("top_n", topN.toString());

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
      // Reset zoom when new heatmap loads
      resetHeatmapView();
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
        resetHeatmapView();
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
    <div className="min-h-screen bg-gray-50">
      {/* Fixed Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg shadow-lg">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">TierSense</h1>
                  <p className="text-sm text-gray-600 font-medium">Enterprise Storage Intelligence</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={handleManualReset}
                variant="outline"
                size="sm"
                className="hover:bg-red-50 border-red-200 text-red-700 hover:text-red-800 hover:border-red-300 font-medium shadow-sm"
              >
                <RefreshCw className="h-4 w-4 mr-2 text-red-600" />
                Reset
              </Button>
              <Dialog open={showSettings} onOpenChange={setShowSettings}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="hover:bg-gray-50 font-medium shadow-sm">
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
                      <Label htmlFor="settings-api-key" className="text-sm font-semibold text-gray-800 mb-3 block">
                        API Key
                      </Label>
                      <div className="relative">
                        <Input
                          id="settings-api-key"
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="Enter your API key"
                          className="pr-10 border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500 transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiKey((v) => !v)}
                          className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600 transition-colors"
                          tabIndex={-1}
                        >
                          {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Tier Ranges */}
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-bold text-gray-800 mb-4">Storage Tier Ranges</h4>
                      {(["HOT", "WARM", "COLD"] as const).map((tier) => (
                        <div key={tier} className="flex items-center gap-3 mb-4">
                          <div className={`px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-sm ${
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
                            className="w-20 h-8 border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500"
                          />
                          <span className="text-gray-400 font-bold">—</span>
                          <Input
                            type="number"
                            min={0}
                            placeholder="max"
                            value={tierRanges[tier][1] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value === "" ? null : parseInt(e.target.value, 10);
                              setTierRanges((prev) => ({ ...prev, [tier]: [prev[tier][0], v] }));
                            }}
                            className="w-20 h-8 border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500"
                          />
                        </div>
                      ))}
                      {tierError && <p className="text-xs text-red-600 mt-2 font-medium">{tierError}</p>}
                      <Button
                        className="w-full mt-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
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
      <div className="flex pt-20">
        {/* Resizable Left Sidebar */}
        <aside 
          ref={sidebarRef}
          className={`fixed left-0 top-20 h-screen bg-white border-r border-gray-200 overflow-hidden transition-all duration-200 shadow-lg ${
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
              className="absolute top-4 right-2 z-10 h-8 w-8 p-0 hover:bg-gray-100 rounded-full shadow-sm"
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
                <div className="mb-8">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="p-2 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg shadow-lg">
                      <Zap className="h-5 w-5 text-white" />
                    </div>
                    <h2 className="text-lg font-bold text-gray-900">Analysis Setup</h2>
                  </div>
                  <div className="h-1 w-full bg-gradient-to-r from-blue-600 to-blue-700 rounded-full shadow-sm"></div>
                </div>

                <div className="space-y-8">
                  <div>
                    <Label htmlFor="llm-select" className="text-sm font-bold text-gray-800 mb-3 block">
                      AI Model Provider
                    </Label>
                    <Select value={selectedLLM} onValueChange={setSelectedLLM}>
                      <SelectTrigger className="border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500 transition-colors font-medium shadow-sm">
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

                  {/* Enhanced Directory Selection - UPDATED TO REMOVE CUSTOM PATH */}
                  <div>
                    <Label className="text-sm font-bold text-gray-800 mb-3 block">
                      Target Directory
                    </Label>
                    <div className="space-y-4">
                      <Select value={selectedDirectoryType} onValueChange={handleDirectoryTypeChange}>
                        <SelectTrigger className="border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500 transition-colors font-medium shadow-sm">
                          <SelectValue placeholder="Choose directory type" />
                        </SelectTrigger>
                        <SelectContent>
                          {commonDirectories.map((dir) => (
                            <SelectItem key={dir.value} value={dir.value}>
                              <div className="flex items-center space-x-2">
                                {dir.icon}
                                <span className="font-medium">{dir.label}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {selectedDirectory && (
                        <div className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200 shadow-sm">
                          <div className="flex items-center space-x-2 text-sm text-gray-700 mb-2">
                            <HardDrive className="h-4 w-4 text-blue-600" />
                            <span className="font-bold">Selected Path:</span>
                          </div>
                          <code className="text-xs text-gray-800 font-mono bg-white p-3 rounded-lg border shadow-sm block">
                            {selectedDirectory}
                          </code>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-3 leading-relaxed font-medium">
                      Audit rules will be automatically configured for the selected directory
                    </p>
                  </div>

                  <Button
                    onClick={handleRunAnalysis}
                    disabled={!selectedLLM || isAnalyzing || !apiKey || !selectedDirectory}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 py-4 font-bold text-base shadow-lg hover:shadow-xl transition-all duration-200"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Play className="h-5 w-5 mr-3" />
                        Run Analysis
                      </>
                    )}
                  </Button>
                  {apiKeyWarning && (
                    <div className="p-4 bg-red-50 border-l-4 border-red-400 rounded-r-lg shadow-sm">
                      <p className="text-sm text-red-700 font-semibold">{apiKeyWarning}</p>
                    </div>
                  )}

                  {/* Enterprise Features - Enhanced with Better Styling */}
                  <div className="mt-8 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-lg">
                    <h3 className="text-base font-black text-blue-900 mb-5 flex items-center space-x-3">
                      <div className="p-2 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg shadow-lg">
                        <TrendingUp className="h-5 w-5 text-white" />
                      </div>
                      <span>Enterprise Features</span>
                    </h3>
                    <ul className="space-y-3">
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">Multi-directory analysis support</span>
                      </li>
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">Automated audit rule configuration</span>
                      </li>
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">Real-time file access monitoring</span>
                      </li>
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">AI-powered tier recommendations</span>
                      </li>
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">Historical trend analysis</span>
                      </li>
                      <li className="text-sm text-blue-800 flex items-start space-x-3 leading-relaxed">
                        <div className="w-2 h-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full mt-2 shadow-sm flex-shrink-0"></div>
                        <span className="font-semibold">Cost optimization insights</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Collapsed State Icon */}
            {isCollapsed && (
              <div className="flex flex-col items-center justify-center h-full space-y-4">
                <div className="p-3 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl shadow-lg">
                  <Zap className="h-7 w-7 text-blue-600" />
                </div>
                <div className="writing-mode-vertical text-sm font-bold text-gray-600 transform rotate-180">
                  Analysis
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
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg shadow-lg mr-4">
                        <Calendar className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-blue-800">Real-time Analytics Active</h3>
                        <p className="text-sm text-blue-600 mt-2 font-medium">
                          Access patterns refresh daily at {dailyResetInfo.resetTime} | Current session: {dailyResetInfo.date}
                        </p>
                        {dailyResetInfo.message && (
                          <p className="text-sm text-blue-600 mt-1 font-medium">{dailyResetInfo.message}</p>
                        )}
                        {results.search_info?.directory && (
                          <p className="text-sm text-blue-600 mt-2 font-medium">
                            Monitoring directory: <code className="bg-blue-100 px-2 py-1 rounded font-mono text-xs">{results.search_info.directory}</code>
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Summary Statistics */}
              <Card className="shadow-lg border-gray-200">
                <CardHeader className="flex items-center justify-between bg-gradient-to-r from-gray-50 to-gray-100 rounded-t-lg">
                  <CardTitle className="text-xl font-bold text-gray-900">
                    {results.search_info?.title || "Storage Analysis Summary"}
                  </CardTitle>
                  <Button onClick={exportResults} variant="outline" size="sm" className="font-semibold shadow-sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="grid grid-cols-4 gap-6">
                    <div className="text-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl shadow-sm border border-gray-200">
                      <div className="text-3xl font-black text-gray-900">
                        {(results.summary?.total_files ?? results.search_info?.total_files ?? 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600 mt-2 font-bold">Total Files</div>
                    </div>
                    <div className="text-center p-6 bg-gradient-to-br from-red-50 to-red-100 rounded-xl shadow-sm border border-red-200">
                      <div className="text-3xl font-black text-red-600">
                        {results.summary?.hot_tier ?? 0}
                      </div>
                      <div className="text-sm text-red-600 mt-2 font-bold">HOT</div>
                    </div>
                    <div className="text-center p-6 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl shadow-sm border border-orange-200">
                      <div className="text-3xl font-black text-orange-600">
                        {results.summary?.warm_tier ?? 0}
                      </div>
                      <div className="text-sm text-orange-600 mt-2 font-bold">WARM</div>
                    </div>
                    <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-sm border border-blue-200">
                      <div className="text-3xl font-black text-blue-600">
                        {results.summary?.cold_tier ?? 0}
                      </div>
                      <div className="text-sm text-blue-600 mt-2 font-bold">COLD</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Heatmap & Filters with Zoom Controls */}
              <Card className="shadow-lg border-gray-200">
                <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-t-lg">
                  <CardTitle className="flex items-center text-xl font-bold text-gray-900">
                    <BarChart3 className="h-6 w-6 mr-3 text-blue-600" />
                    Access Heatmap & Filters
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6 p-6">
                  {/* Filter Controls */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center mb-4 space-x-3">
                      <div className="p-2 bg-gradient-to-br from-gray-600 to-gray-700 rounded-lg shadow-lg">
                        <Filter className="h-4 w-4 text-white" />
                      </div>
                      <span className="text-base font-bold text-gray-800">Visualization Controls</span>
                    </div>
                    <div className="flex flex-wrap items-end gap-4">
                      <div>
                        <Label className="text-xs text-gray-600 font-bold">Search Type</Label>
                        <Select value={searchType} onValueChange={setSearchType}>
                          <SelectTrigger className="h-9 w-36 border-2 border-gray-200 hover:border-blue-300 font-medium">
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
                        <Label className="text-xs text-gray-600 font-bold">Display Count</Label>
                        <Select value={topN.toString()} onValueChange={(v) => setTopN(+v)}>
                          <SelectTrigger className="h-9 w-28 border-2 border-gray-200 hover:border-blue-300 font-medium">
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
                          <Label className="text-xs text-gray-600 font-bold">Select Date</Label>
                          <Select value={selectedDate} onValueChange={setSelectedDate}>
                            <SelectTrigger className="h-9 w-36 border-2 border-gray-200 hover:border-blue-300 font-medium">
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
                            <Label className="text-xs text-gray-600 font-bold">Start Date</Label>
                            <Input
                              type="date"
                              value={startDate}
                              onChange={(e) => setStartDate(e.target.value)}
                              className="h-9 w-40 border-2 border-gray-200 hover:border-blue-300 font-medium"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-gray-600 font-bold">End Date</Label>
                            <Input
                              type="date"
                              value={endDate}
                              onChange={(e) => setEndDate(e.target.value)}
                              className="h-9 w-40 border-2 border-gray-200 hover:border-blue-300 font-medium"
                            />
                          </div>
                        </>
                      )}
                      {searchType === "pattern" && (
                        <div>
                          <Label className="text-xs text-gray-600 font-bold">File Pattern</Label>
                          <Input
                            placeholder="e.g., .log, report"
                            value={filePattern}
                            onChange={(e) => setFilePattern(e.target.value)}
                            className="h-9 w-52 border-2 border-gray-200 hover:border-blue-300 font-medium"
                          />
                        </div>
                      )}
                      <div className="flex ml-auto space-x-3">
                        <Button onClick={clearSearch} variant="outline" size="sm" className="h-9 font-semibold shadow-sm">
                          Clear
                        </Button>
                        <Button
                          onClick={handleAdvancedSearch}
                          disabled={isSearching}
                          size="sm"
                          className="h-9 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 font-semibold shadow-lg"
                        >
                          <Search className="h-4 w-4 mr-2" />
                          {isSearching ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border border-white border-t-transparent mr-2"></div>
                              Searching...
                            </>
                          ) : (
                            "Apply"
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Heatmap Display with Zoom Controls */}
                  <div className="bg-white rounded-xl border border-gray-200 shadow-lg">
                    {/* Zoom Controls */}
                    {heatmapUrl && (
                      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100 rounded-t-xl">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-700 font-bold">Zoom:</span>
                          <Button
                            onClick={handleZoomOut}
                            disabled={heatmapZoom <= 50}
                            variant="outline"
                            size="sm"
                            className="h-8 w-8 p-0 shadow-sm"
                          >
                            <ZoomOut className="h-4 w-4" />
                          </Button>
                          <span className="text-sm font-black text-gray-800 min-w-[60px] text-center bg-white px-3 py-1 rounded-lg border shadow-sm">
                            {heatmapZoom}%
                          </span>
                          <Button
                            onClick={handleZoomIn}
                            disabled={heatmapZoom >= 300}
                            variant="outline"
                            size="sm"
                            className="h-8 w-8 p-0 shadow-sm"
                          >
                            <ZoomIn className="h-4 w-4" />
                          </Button>
                          <Button
                            onClick={resetHeatmapView}
                            variant="outline"
                            size="sm"
                            className="h-8 px-3 font-semibold shadow-sm"
                          >
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Reset
                          </Button>
                        </div>
                        <div className="text-xs text-gray-600 font-medium">
                          {heatmapZoom > 100 && "Click and drag to pan"}
                        </div>
                      </div>
                    )}
                    
                    {/* Heatmap Container */}
                    <div 
                      ref={heatmapContainerRef}
                      className="relative overflow-hidden"
                      style={{ height: "600px" }}
                    >
                      {heatmapUrl ? (
                        <div
                          className={`absolute inset-0 flex items-center justify-center ${
                            heatmapZoom > 100 ? 'cursor-move' : 'cursor-default'
                          }`}
                          onMouseDown={handleMouseDown}
                          onMouseMove={handleMouseMove}
                          onMouseUp={handleMouseUp}
                          onMouseLeave={handleMouseUp}
                        >
                          <img
                            src={heatmapUrl}
                            alt="Access Heatmap"
                            className="max-w-none transition-transform duration-200"
                            style={{
                              transform: `scale(${heatmapZoom / 100}) translate(${heatmapPosition.x}px, ${heatmapPosition.y}px)`,
                              transformOrigin: 'center center'
                            }}
                            onError={(e) => {
                              console.error("Heatmap failed to load");
                              e.currentTarget.style.display = "none";
                            }}
                            draggable={false}
                          />
                        </div>
                      ) : (
                        <div className="h-full flex items-center justify-center text-gray-500">
                          <div className="text-center">
                            <BarChart3 className="mx-auto mb-6 h-20 w-20 opacity-30" />
                            <p className="text-xl font-bold text-gray-700">Intelligence Visualization</p>
                            <p className="text-base text-gray-600 mt-2 font-medium">Run analysis to generate enterprise storage insights</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Enhanced AI File Analysis Results */}
              {results.analysis?.length > 0 && (
                <Card className="shadow-lg border-gray-200">
                  <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-t-lg">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl font-bold text-gray-900">
                        AI Classification Results
                      </CardTitle>
                      <div className="flex items-center space-x-2">
                        <Button
                          onClick={() => setSuggestionsViewMode('grid')}
                          variant={suggestionsViewMode === 'grid' ? 'default' : 'outline'}
                          size="sm"
                          className="h-9 w-9 p-0 shadow-sm"
                        >
                          <Grid3X3 className="h-4 w-4" />
                        </Button>
                        <Button
                          onClick={() => setSuggestionsViewMode('list')}
                          variant={suggestionsViewMode === 'list' ? 'default' : 'outline'}
                          size="sm"
                          className="h-9 w-9 p-0 shadow-sm"
                        >
                          <List className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6">
                    {suggestionsViewMode === 'grid' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-5 border border-gray-200 rounded-xl bg-white hover:shadow-lg transition-shadow duration-200"
                          >
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex-1 mr-3">
                                <h4 className="font-bold text-sm text-gray-900 break-words">
                                  {file.path.split('/').pop() || file.path}
                                </h4>
                                <p className="text-xs text-gray-500 mt-2 break-all font-medium">
                                  {file.path}
                                </p>
                                {/* SHOW AI SUGGESTION */}
                                {file.suggestion && (
                                  <p className="text-xs text-blue-700 mt-3 bg-blue-50 p-3 rounded-lg border border-blue-200">
                                    <strong>Suggestion:</strong> {file.suggestion}
                                  </p>
                                )}
                              </div>
                              <span
                                className={`px-3 py-1.5 text-xs font-bold rounded-full flex-shrink-0 shadow-sm ${getTierColor(file.tier)}`}
                              >
                                {file.tier}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-xs text-gray-600">
                              <span className="font-semibold">Access: {file.access_frequency}</span>
                              <span className="font-semibold">Score: {file.score || 0}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {results.analysis.map((file: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-4 border border-gray-200 rounded-xl bg-white hover:bg-gray-50 transition-colors duration-200"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="font-bold text-sm text-gray-900 truncate">
                                {file.path}
                              </div>
                              <div className="text-xs text-gray-500 mt-2 flex items-center space-x-6">
                                <span className="font-semibold">Access frequency: {file.access_frequency}</span>
                                <span className="font-semibold">Score: {file.score || 0}</span>
                              </div>
                              {/* SHOW AI SUGGESTION IN LIST VIEW TOO */}
                              {file.suggestion && (
                                <div className="text-xs text-blue-700 mt-2 font-medium">
                                  <strong>Suggestion:</strong> {file.suggestion}
                                </div>
                              )}
                            </div>
                            <span
                              className={`px-4 py-2 text-xs font-bold rounded-full ml-4 flex-shrink-0 shadow-sm ${getTierColor(file.tier)}`}
                            >
                              {file.tier}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="mt-6 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 shadow-sm">
                      <p className="text-sm text-blue-800 font-semibold leading-relaxed">
                        <strong>AI Recommendations:</strong> Files are classified based on access patterns. 
                        HOT tier files should be on fast storage, WARM tier on standard storage, 
                        and COLD tier can be archived to reduce costs.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* JSON Output */}
              <Card className="shadow-lg border-gray-200">
                <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-t-lg">
                  <CardTitle className="flex items-center text-xl font-bold text-gray-900">
                    <FileText className="h-6 w-6 mr-3 text-blue-600" />
                    Raw JSON Output
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <Textarea
                    value={JSON.stringify(results, null, 2)}
                    readOnly
                    className="h-64 resize-none font-mono text-sm bg-gray-50 border-2 border-gray-200"
                  />
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="h-96 flex items-center justify-center shadow-lg border-gray-200">
              <div className="text-center text-gray-500">
                <BarChart3 className="mx-auto mb-8 h-24 w-24 opacity-30" />
                <p className="text-2xl font-bold text-gray-700">Ready for Enterprise Analysis</p>
                <p className="text-base text-gray-600 mt-4 font-medium">
                  Configure your AI model and target directory in the analysis panel, then run intelligent storage tiering analysis
                </p>
              </div>
            </Card>
          )}
        </main>
      </div>

      {/* Enhanced Loading Overlay */}
      {(isAnalyzing || isSearching) && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
          <div className="bg-white rounded-xl shadow-2xl p-10 flex flex-col items-center space-y-6 border border-gray-200">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent shadow-lg"></div>
            <div className="text-xl font-bold text-gray-800">
              {isAnalyzing ? "Analyzing..." : "Searching..."}
            </div>
            <div className="text-base text-gray-600 font-medium">
              {isAnalyzing ? "Processing your data" : "Finding results"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
