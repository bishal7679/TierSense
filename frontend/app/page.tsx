"use client";

import type React from "react";
import { useState, useEffect } from "react";
import { Download, Settings, BarChart3, FileText, Play, Eye, EyeOff, Filter, Search, Calendar, Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label"
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
  
  // Enhanced search and filter state
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [topN, setTopN] = useState(50);
  const [heatmapUrl, setHeatmapUrl] = useState("");
  const [searchEnabled, setSearchEnabled] = useState(false);
  
  // Search filters
  const [searchType, setSearchType] = useState("current");
  const [selectedDate, setSelectedDate] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filePattern, setFilePattern] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load API key and fetch dates
  useEffect(() => {
    const savedKey = localStorage.getItem("tiersense_api_key");
    if (savedKey) setApiKey(savedKey);
    fetchAvailableDates();
  }, []);

  useEffect(() => {
    if (apiKey) localStorage.setItem("tiersense_api_key", apiKey);
  }, [apiKey]);

  // Fetch available dates
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

  // Handle advanced search
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
      
      // Add search-specific parameters
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
          search_info: {
            type: result.search_type,
            title: result.title,
            total_files: result.total_files,
            displayed_files: result.displayed_files
          }
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

  // Main analysis function
  const handleRunAnalysis = async () => {
    if (!apiKey) {
      setApiKeyWarning("API Key is required to run analysis.");
      return;
    }

    const formData = new FormData();
    formData.append("llm", selectedLLM);
    formData.append("api_key", apiKey);
    formData.append("top_n", topN.toString());

    let monitorPath: string | null = null;

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
      monitorPath = rawDir.startsWith("/host-root")
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
        } catch { /* ignore */ }
        setApiKeyWarning(errorMsg);
        return;
      }
      
      const result = await response.json();
      setResults(result);
      setHeatmapUrl(`${apiUrl}${result.heatmap}?ts=${Date.now()}`);
      setSearchEnabled(result.search_enabled || false);
      
      // Refresh available dates after analysis
      fetchAvailableDates();
    } catch (err) {
      setApiKeyWarning(err instanceof Error ? err.message : "Failed to run analysis.");
    } finally {
      setIsAnalyzing(false);
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
      case "HOT": return "bg-red-500";
      case "WARM": return "bg-yellow-500";
      case "COLD": return "bg-blue-500";
      default: return "bg-gray-500";
    }
  };

  const clearSearch = () => {
    setSearchType("current");
    setSelectedDate("");
    setStartDate("");
    setEndDate("");
    setFilePattern("");
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
                  <Button onClick={() => setShowSettings(false)} className="w-full">
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
                  <Label htmlFor="api-key">API Key</Label>
                  <div className="relative">
                    <Input
                      id="api-key"
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter API key"
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
                  {apiKeyWarning && (
                    <p className="text-xs text-red-600 mt-1">{apiKeyWarning}</p>
                  )}
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
                        <Label htmlFor="selectedDirectory" className="text-sm">Directory Path</Label>
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
                        <p className="mt-2 text-sm text-slate-600">
                          Selected: {uploadedFile.name}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <Button
                  onClick={handleRunAnalysis}
                  disabled={!selectedLLM || isAnalyzing}
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
                      {results.search_info?.title || "Analysis Summary"}
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
                          {results?.summary?.total_files ?? results?.search_info?.displayed_files ?? 0}
                        </div>
                        <div className="text-sm text-slate-600">Total Files</div>
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

                {/* Enhanced Search and Filter Controls - Above Heatmap */}
                {searchEnabled && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg font-medium flex items-center">
                        <Filter className="h-5 w-5 mr-2" />
                        Heatmap Search & Filters
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        {/* Search Type */}
                        <div>
                          <Label>Search Type</Label>
                          <Select value={searchType} onValueChange={setSearchType}>
                            <SelectTrigger>
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

                        {/* Top N Files */}
                        <div>
                          <Label>Show Files</Label>
                          <Select value={topN.toString()} onValueChange={(v) => setTopN(parseInt(v))}>
                            <SelectTrigger>
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

                        {/* Conditional Date/Pattern Fields */}
                        {searchType === "date" && (
                          <div>
                            <Label>Select Date</Label>
                            <Select value={selectedDate} onValueChange={setSelectedDate}>
                              <SelectTrigger>
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
                              <Label>Start Date</Label>
                              <Input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                              />
                            </div>
                            <div>
                              <Label>End Date</Label>
                              <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                              />
                            </div>
                          </>
                        )}

                        {searchType === "pattern" && (
                          <div>
                            <Label>File Pattern</Label>
                            <Input
                              placeholder="e.g., .log, report, temp"
                              value={filePattern}
                              onChange={(e) => setFilePattern(e.target.value)}
                            />
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-end space-x-2">
                        <Button onClick={clearSearch} variant="outline" size="sm">
                          Clear
                        </Button>
                        <Button
                          onClick={handleAdvancedSearch}
                          disabled={isSearching}
                          className="flex items-center"
                        >
                          <Search className="h-4 w-4 mr-2" />
                          {isSearching ? "Searching..." : "Apply Search"}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Heatmap - Always Displayed After Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg font-medium flex items-center">
                      <BarChart3 className="h-5 w-5 mr-2" />
                      Access Heatmap
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-center">
                    {heatmapUrl ? (
                      <img
                        src={heatmapUrl}
                        alt="Access Heatmap"
                        className="mx-auto rounded border border-gray-300 max-w-full"
                        style={{ maxHeight: "600px", objectFit: "contain" }}
                        onError={(e) => {
                          console.error("Heatmap failed to load");
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="text-slate-500 py-8">
                        <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Heatmap will appear here after analysis</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Analysis Results */}
                {results?.analysis && results.analysis.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg font-medium">File Analysis Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {results.analysis.map((file: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex-1">
                              <div className="font-medium text-sm">{file.path}</div>
                              <div className="text-xs text-slate-500">
                                Access frequency: {file.access_frequency}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2 py-1 text-xs rounded text-white ${getTierColor(file.tier)}`}
                              >
                                {file.tier}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

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
                  <p className="text-sm">Configure your settings and run an analysis to see results</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>

      {(isAnalyzing || isSearching) && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 flex flex-col items-center shadow-lg">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mb-4"></div>
            <div className="text-lg font-medium text-slate-800">
              {isAnalyzing ? "TierSense is analyzing your data..." : "Searching heatmaps..."}
            </div>
            <div className="text-sm text-slate-500 mt-2">This may take a few moments</div>
          </div>
        </div>
      )}
    </div>
  );
}
