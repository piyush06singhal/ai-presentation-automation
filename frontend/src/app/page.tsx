"use client";

import React, { useState, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, 
  FileSpreadsheet, 
  ChevronRight, 
  AlertTriangle, 
  Activity, 
  Settings, 
  Eye, 
  Trash2, 
  ArrowUp, 
  ArrowDown, 
  RefreshCw, 
  Download, 
  ShieldCheck, 
  BarChart, 
  Layers, 
  Sliders, 
  Plus, 
  CheckCircle,
  Clock,
  Sparkles,
  RefreshCcw,
  BookOpen
} from "lucide-react";

// Get base API URL from environment, fallback to localhost for development
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ColumnSchema {
  name: string;
  datatype: string;
}

interface WorksheetMetadata {
  name: string;
  columns: ColumnSchema[];
  row_count: number;
  col_count: number;
  is_empty: boolean;
}

interface HealthIssue {
  severity: string;
  warning: string;
  recommendation: string;
  worksheet: string;
  column?: string;
}

interface WorkbookHealth {
  issues: HealthIssue[];
  overall_score: number;
}

interface DetectedKPI {
  name: string;
  value: number;
  column: string;
  worksheet: string;
  confidence: number;
  unit?: string;
  description: string;
}

interface BusinessTrend {
  metric: string;
  direction: string;
  percentage_change: number;
  time_col: string;
  growth_rate: number;
  description: string;
  worksheet: string;
}

interface BusinessFact {
  fact_id: string;
  statement: string;
  source_worksheet: string;
  metrics: string[];
  importance: number;
}

interface BusinessSummary {
  metadata: {
    sheets: WorksheetMetadata[];
    file_size_bytes: number;
    active_sheets_count: number;
  };
  health: WorkbookHealth;
  kpis: DetectedKPI[];
  trends: BusinessTrend[];
  facts: BusinessFact[];
}

interface SlidePlan {
  slide_id: string;
  template_id: string;
  title: string;
  objective: string;
  worksheet: string;
  chart_type?: string | null;
  x_axis?: string | null;
  y_axis?: string[] | null;
  insights: string[];
  required_kpis?: string[] | null;
  recommendations?: string[] | null;
  speaker_notes: string;
  why_created: string;
  priority: number;
  confidence: number;
}

interface StoryboardRequest {
  audience: string;
  objective: string;
  slides: SlidePlan[];
}

export default function DeckMateApp() {
  // Stepper state: 0=Landing/Upload, 1=BI Setup, 2=Storyboard Preview, 3=Success
  const [step, setStep] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // File & BI State
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<BusinessSummary | null>(null);

  // Config parameters
  const [audience, setAudience] = useState<string>("CEO");
  const [objective, setObjective] = useState<string>("Analyze performance trends, cost margins, and outline strategic next steps.");
  const [slideCount, setSlideCount] = useState<number>(5);
  const [deckTitle, setDeckTitle] = useState<string>("");
  const [deckSubtitle, setDeckSubtitle] = useState<string>("");
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Storyboard Preview State
  const [storyboard, setStoryboard] = useState<StoryboardRequest | null>(null);
  
  // Drag and drop highlights
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Benchmarking / Stats state
  const [timeTakenMs, setTimeTakenMs] = useState<number>(0);

  // Reset complete workspace
  const handleReset = () => {
    setFile(null);
    setSummary(null);
    setStoryboard(null);
    setStep(0);
    setErrorMsg(null);
    setLoading(false);
  };

  // Drag handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setErrorMsg(null);
    if (!selectedFile.name.endsWith(".xlsx") && !selectedFile.name.endsWith(".xlsm")) {
      setErrorMsg("Supported format error: Please upload a valid Excel workbook file (.xlsx, .xlsm).");
      return;
    }
    setFile(selectedFile);
    // Auto trigger analysis
    uploadAndAnalyze(selectedFile);
  };

  // Step 1: Upload and Analyze Excel workbook
  const uploadAndAnalyze = async (excelFile: File) => {
    setLoading(true);
    setErrorMsg(null);
    setLoadingMessage("Uploading Excel workbook data...");
    
    const startTime = Date.now();
    const formData = new FormData();
    formData.append("file", excelFile);

    try {
      setLoadingMessage("Analyzing spreadsheets & calculating facts...");
      const response = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setSummary(response.data);
      setStep(1);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Network Failure: Unable to analyze the workbook. Check backend status.");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Query LLM for storyboard planning
  const generateStoryboard = async () => {
    if (!summary) return;
    setLoading(true);
    setErrorMsg(null);
    setLoadingMessage("AI Planning: Assembling narrative script slides...");

    try {
      const response = await axios.post(`${API_BASE}/api/plan`, {
        summary,
        audience,
        objective,
        slide_count: slideCount
      });
      
      const payload: StoryboardRequest = response.data;
      
      // Inject Title & Subtitle override if user added them
      if (deckTitle.trim() && payload.slides.length > 0) {
        payload.slides[0].title = deckTitle;
      }
      if (deckSubtitle.trim() && payload.slides.length > 0) {
        payload.slides[0].objective = deckSubtitle;
      }

      setStoryboard(payload);
      setStep(2);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Groq Timeout / API Error: Storyboard planning failed.");
    } finally {
      setLoading(false);
    }
  };

  // Storyboard editing helpers (stateless updates)
  const removeSlide = (index: number) => {
    if (!storyboard) return;
    const newSlides = [...storyboard.slides];
    newSlides.splice(index, 1);
    setStoryboard({ ...storyboard, slides: newSlides });
  };

  const moveSlide = (index: number, direction: "up" | "down") => {
    if (!storyboard) return;
    const newSlides = [...storyboard.slides];
    const targetIdx = direction === "up" ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= newSlides.length) return;
    
    // Swap slides
    const temp = newSlides[index];
    newSlides[index] = newSlides[targetIdx];
    newSlides[targetIdx] = temp;
    
    setStoryboard({ ...storyboard, slides: newSlides });
  };

  const regenerateSlide = async (index: number) => {
    if (!storyboard || !summary) return;
    setLoading(true);
    setLoadingMessage(`Regenerating layout plan for Slide ${index + 1}...`);
    
    try {
      // Small individual prompt query or calling layout rotation:
      // We can query a single replanner endpoint, or mock layout regeneration cleanly.
      // To ensure stateless reliability, we call /api/plan with 1 target slide count
      // and splice it in.
      const response = await axios.post(`${API_BASE}/api/plan`, {
        summary,
        audience,
        objective: `Regenerate slide for section. Context: ${storyboard.slides[index].why_created}`,
        slide_count: 1
      });
      
      const newSlide = response.data.slides[0];
      if (newSlide) {
        const newSlides = [...storyboard.slides];
        newSlides[index] = newSlide;
        setStoryboard({ ...storyboard, slides: newSlides });
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Failed to regenerate slide details.");
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Approve & Compile PowerPoint slide deck binary
  const compilePowerPoint = async () => {
    if (!file || !storyboard || !summary) return;
    setLoading(true);
    setErrorMsg(null);
    setLoadingMessage("Compiling PowerPoint: Generating native slide shapes...");

    const startTime = Date.now();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("storyboard", JSON.stringify(storyboard));
    formData.append("summary", JSON.stringify(summary));

    try {
      const response = await axios.post(`${API_BASE}/api/generate`, formData, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      const timeMs = Date.now() - startTime;
      setTimeTakenMs(timeMs);

      // Create download anchor trigger link
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${file.name.replace(/\.[^/.]+$/, "")}_deckmate.pptx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      
      setStep(3);
    } catch (err: any) {
      console.error(err);
      setErrorMsg("PowerPoint generation failure: Unable to draw PPTX slide shapes.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Sleek Corporate Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={handleReset}>
            <div className="p-2 bg-sky-500/10 rounded-lg border border-sky-500/30">
              <Layers className="h-6 w-6 text-sky-400" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent">
                DeckMate
              </span>
              <span className="text-xs block text-slate-500">Presentation Automation</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="text-xs text-slate-400 bg-slate-800/80 px-3 py-1 rounded-full border border-slate-700/50">
              Stateless Architecture
            </div>
          </div>
        </div>
      </header>

      {/* Main Core Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-10 flex flex-col justify-center">
        
        {/* Loading Spinner Overlays */}
        {loading && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex flex-col items-center justify-center z-50">
            <div className="relative">
              <div className="h-20 w-20 rounded-full border-2 border-sky-500/20 border-t-sky-500 animate-spin"></div>
              <Sparkles className="absolute inset-0 m-auto h-8 w-8 text-sky-400 animate-pulse" />
            </div>
            <p className="mt-6 text-lg font-medium text-slate-300 animate-pulse">{loadingMessage}</p>
          </div>
        )}

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="mb-8 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-3 text-rose-300">
            <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-sm">System Operations Alert</h4>
              <p className="text-sm opacity-90 mt-1">{errorMsg}</p>
            </div>
            <button 
              className="text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 px-3 py-1.5 rounded-lg transition"
              onClick={handleReset}
            >
              Reset Page
            </button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* STEP 0: Upload & Landing Page */}
          {step === 0 && (
            <motion.div 
              key="step0"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center"
            >
              {/* Left Column: Premium Pitch */}
              <div className="lg:col-span-6 space-y-6">
                <div className="inline-flex items-center space-x-2 bg-sky-500/10 border border-sky-500/20 px-3 py-1 rounded-full text-xs text-sky-400">
                  <Sparkles className="h-3 w-3" />
                  <span>Excel to PowerPoint Storyboards</span>
                </div>
                
                <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight tracking-tight text-white">
                  Translate Spreadsheet metrics into <span className="bg-gradient-to-r from-sky-400 via-indigo-400 to-emerald-400 bg-clip-text text-transparent">Editable Slide Decks</span>
                </h1>
                
                <p className="text-slate-400 text-lg leading-relaxed">
                  Upload your Excel workbooks to run static data intelligence audits. DeckMate analyzes layouts, identifies metrics, maps trends, and orchestrates slides storyboard grids without saving your data.
                </p>

                {/* Features Highlights */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                  <div className="flex items-start space-x-3 bg-slate-900/40 p-3 rounded-lg border border-slate-800/80">
                    <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block text-sm text-slate-200">100% Native Elements</span>
                      <span className="text-xs text-slate-500">Fully editable text, tables, and shapes.</span>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3 bg-slate-900/40 p-3 rounded-lg border border-slate-800/80">
                    <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block text-sm text-slate-200">Chart Validation Engine</span>
                      <span className="text-xs text-slate-500">Date trends to lines, categories to bars.</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-xs text-slate-500 border-t border-slate-800 pt-6">
                  <ShieldCheck className="h-4 w-4 text-emerald-500" />
                  <span>Privacy Guarantee: stateless workbook analysis. Data is never cached or stored.</span>
                </div>
              </div>

              {/* Right Column: Upload Box */}
              <div className="lg:col-span-6">
                <div 
                  className={`border-2 border-dashed rounded-3xl p-12 text-center transition flex flex-col justify-center items-center h-[380px] bg-slate-900/30 backdrop-blur-sm ${
                    isDragOver 
                      ? "border-sky-400 bg-sky-500/5" 
                      : "border-slate-800 hover:border-slate-700 bg-slate-900/10"
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept=".xlsx,.xlsm"
                    onChange={handleFileSelect} 
                  />
                  
                  <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800 mb-6 group-hover:scale-105 transition">
                    <FileSpreadsheet className="h-10 w-10 text-sky-400" />
                  </div>
                  
                  <h3 className="text-xl font-bold text-white mb-2">Drag and drop workbook</h3>
                  <p className="text-sm text-slate-500 mb-6">
                    Accepts standard Excel files (.xlsx, .xlsm)
                  </p>
                  
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm px-6 py-3 rounded-xl border border-slate-700 transition inline-flex items-center space-x-2"
                  >
                    <span>Browse Workbook</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* STEP 1: Workbook Summary & BI Setup */}
          {step === 1 && summary && (
            <motion.div 
              key="step1"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start"
            >
              {/* Left Column: Config Panel */}
              <div className="lg:col-span-5 bg-slate-900/40 border border-slate-800/80 rounded-3xl p-8 space-y-6">
                <div className="flex items-center space-x-2 text-sky-400">
                  <Settings className="h-5 w-5" />
                  <h2 className="text-xl font-bold text-white">Presentation Configuration</h2>
                </div>

                <div className="space-y-4">
                  {/* Objective */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Presentation Objective
                    </label>
                    <textarea 
                      value={objective} 
                      onChange={(e) => setObjective(e.target.value)}
                      rows={3}
                      className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
                      placeholder="e.g., Outline revenue trajectories and cost structures."
                    />
                  </div>

                  {/* Audience */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Target Audience
                    </label>
                    <select 
                      value={audience} 
                      onChange={(e) => setAudience(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
                    >
                      <option value="CEO">CEO (Strategic Cost cost controls)</option>
                      <option value="Board Members">Board Members (Outlier Focus)</option>
                      <option value="Finance">Finance (Detailed Ledger metrics)</option>
                      <option value="Sales Leadership">Sales Leadership (Sales growth)</option>
                      <option value="Marketing Team">Marketing Team (Engagement)</option>
                      <option value="Operations Team">Operations Team (Capacity lists)</option>
                      <option value="Clients">Clients (Services values)</option>
                      <option value="Investors">Investors (Scaling plans)</option>
                    </select>
                  </div>

                  {/* Slide Count */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Slide Deck count
                      </label>
                      <span className="text-sm font-semibold text-sky-400">{slideCount} Slides</span>
                    </div>
                    <input 
                      type="range" 
                      min="3" 
                      max="12" 
                      value={slideCount}
                      onChange={(e) => setSlideCount(parseInt(e.target.value))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-sky-400"
                    />
                  </div>

                  {/* Collapsible Advanced options */}
                  <div className="border-t border-slate-850 pt-4">
                    <button 
                      onClick={() => setShowAdvanced(!showAdvanced)}
                      className="flex items-center space-x-2 text-xs text-slate-400 hover:text-slate-300 font-semibold"
                    >
                      <Sliders className="h-3.5 w-3.5" />
                      <span>{showAdvanced ? "Hide Advanced Settings" : "Show Advanced Settings"}</span>
                    </button>
                    
                    {showAdvanced && (
                      <div className="mt-4 space-y-4 animate-fadeIn">
                        <div>
                          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Title Override (Optional)
                          </label>
                          <input 
                            type="text" 
                            value={deckTitle}
                            onChange={(e) => setDeckTitle(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
                            placeholder="e.g. FY26 Operational Trajectory"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Subtitle Override (Optional)
                          </label>
                          <input 
                            type="text" 
                            value={deckSubtitle}
                            onChange={(e) => setDeckSubtitle(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
                            placeholder="e.g. Cost and Revenue Analysis"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <button 
                  onClick={generateStoryboard}
                  className="w-full bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-600 hover:to-indigo-600 text-white font-bold py-4 rounded-xl transition flex items-center justify-center space-x-2 shadow-lg shadow-sky-500/10"
                >
                  <Sparkles className="h-5 w-5" />
                  <span>Draft Storyboard Plan</span>
                </button>
              </div>

              {/* Right Column: Workbook summary details */}
              <div className="lg:col-span-7 space-y-8">
                {/* Stats cards grid */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-4 text-center">
                    <span className="text-2xl font-extrabold text-white block">
                      {summary.metadata.active_sheets_count}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">Worksheets</span>
                  </div>
                  <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-4 text-center">
                    <span className="text-2xl font-extrabold text-emerald-400 block">
                      {summary.health.overall_score}%
                    </span>
                    <span className="text-xs text-slate-400 font-medium">Health Rating</span>
                  </div>
                  <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-4 text-center">
                    <span className="text-2xl font-extrabold text-sky-400 block">
                      {summary.kpis.length}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">KPIs Flagged</span>
                  </div>
                </div>

                {/* File Worksheets list */}
                <div className="bg-slate-900/20 border border-slate-800/80 rounded-3xl p-6">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4 inline-flex items-center space-x-2">
                    <BookOpen className="h-4 w-4 text-sky-400" />
                    <span>Workbook Sheet Schemas</span>
                  </h3>
                  
                  <div className="space-y-4">
                    {summary.metadata.sheets.map((sheet, sIdx) => (
                      <div key={sIdx} className="bg-slate-950 p-4 rounded-xl border border-slate-850/50">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <span className="font-bold text-slate-200">{sheet.name}</span>
                            <span className="text-xs block text-slate-500 mt-0.5">
                              {sheet.row_count} Rows × {sheet.col_count} Columns
                            </span>
                          </div>
                          {sheet.is_empty && (
                            <span className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs px-2 py-0.5 rounded">
                              Empty Worksheet
                            </span>
                          )}
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          {sheet.columns.map((col, cIdx) => (
                            <span key={cIdx} className="bg-slate-900 text-xs text-slate-300 px-2 py-1 rounded border border-slate-800">
                              {col.name} <span className="text-slate-500 font-mono">({col.datatype})</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Health warnings alert panel */}
                {summary.health.issues.length > 0 && (
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-3xl p-6">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-400 mb-4 inline-flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span>Data Quality Warnings</span>
                    </h3>
                    
                    <div className="space-y-3">
                      {summary.health.issues.map((issue, idx) => (
                        <div key={idx} className="bg-slate-950 p-3.5 rounded-xl border border-slate-850/50 flex items-start space-x-3 text-slate-300">
                          <Activity className="h-4 w-4 text-amber-500 mt-1 flex-shrink-0" />
                          <div>
                            <span className="font-semibold block text-sm text-slate-200">{issue.warning}</span>
                            <span className="text-xs text-slate-400 block mt-0.5">
                              Sheet: {issue.worksheet} • Recommendation: {issue.recommendation}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* STEP 2: Storyboard Preview & Draggable Index Card grid */}
          {step === 2 && storyboard && (
            <motion.div 
              key="step2"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              {/* Objective Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/30 p-6 rounded-3xl border border-slate-800/80">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                    <Eye className="h-5 w-5 text-sky-400" />
                    <span>Storyboard Layout Preview</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Audience: <strong className="text-slate-200">{audience}</strong> • Objective: <strong className="text-slate-200">{objective}</strong>
                  </p>
                </div>
                
                <div className="flex items-center space-x-3">
                  <button 
                    onClick={handleReset}
                    className="bg-slate-850 hover:bg-slate-800 px-4 py-2.5 rounded-lg border border-slate-700/50 text-xs font-semibold inline-flex items-center space-x-1.5 transition"
                  >
                    <RefreshCcw className="h-3.5 w-3.5" />
                    <span>Upload New</span>
                  </button>
                  
                  <button 
                    onClick={compilePowerPoint}
                    className="bg-sky-500 hover:bg-sky-600 text-white px-5 py-2.5 rounded-lg text-xs font-bold inline-flex items-center space-x-1.5 transition shadow-lg shadow-sky-500/20"
                  >
                    <Download className="h-4 w-4" />
                    <span>Generate Presentation</span>
                  </button>
                </div>
              </div>

              {/* Storyboard cards lists */}
              <div className="space-y-4">
                {storyboard.slides.map((slide, index) => (
                  <div 
                    key={slide.slide_id} 
                    className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 relative flex flex-col md:flex-row gap-6 hover:border-slate-700/80 transition"
                  >
                    {/* Index order sidebar */}
                    <div className="flex md:flex-col items-center justify-between md:justify-center gap-2 border-b md:border-b-0 md:border-r border-slate-800/80 pb-4 md:pb-0 pr-0 md:pr-6 md:w-16">
                      <span className="text-2xl font-extrabold text-slate-500">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      
                      <div className="flex md:flex-col gap-1">
                        <button 
                          disabled={index === 0}
                          onClick={() => moveSlide(index, "up")}
                          className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded disabled:opacity-30 disabled:hover:bg-transparent transition"
                        >
                          <ArrowUp className="h-4 w-4" />
                        </button>
                        <button 
                          disabled={index === storyboard.slides.length - 1}
                          onClick={() => moveSlide(index, "down")}
                          className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded disabled:opacity-30 disabled:hover:bg-transparent transition"
                        >
                          <ArrowDown className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={() => regenerateSlide(index)}
                          className="p-1 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded transition"
                          title="Regenerate Layout Plan"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={() => removeSlide(index)}
                          className="p-1 text-slate-400 hover:text-rose-400 hover:bg-slate-850 rounded transition"
                          title="Remove Slide"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>

                    {/* Slide detailed config info */}
                    <div className="flex-1 space-y-4">
                      {/* Top Info */}
                      <div className="flex flex-wrap justify-between items-start gap-2">
                        <div>
                          <span className="bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs px-2.5 py-1 rounded-md font-semibold font-mono tracking-wider">
                            LAYOUT: {slide.template_id.toUpperCase()}
                          </span>
                          <h3 className="text-lg font-bold text-white mt-2">
                            {slide.title}
                          </h3>
                        </div>
                        
                        <div className="flex items-center space-x-2 text-xs text-slate-500">
                          <span>Confidence: {(slide.confidence * 100).toFixed(0)}%</span>
                          <span>•</span>
                          <span>Priority: {slide.priority}</span>
                        </div>
                      </div>

                      {/* Visual Mapping info */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-950 p-4 rounded-xl border border-slate-850/50">
                        <div>
                          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                            Source Worksheet
                          </span>
                          <span className="font-semibold block text-sm text-slate-300 mt-0.5">
                            {slide.worksheet}
                          </span>
                        </div>

                        {slide.chart_type && slide.chart_type.toLowerCase() !== "none" ? (
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider inline-flex items-center space-x-1">
                              <BarChart className="h-3 w-3" />
                              <span>Chart Configuration</span>
                            </span>
                            <span className="font-semibold block text-sm text-slate-300 mt-0.5">
                              {slide.chart_type} Chart ({slide.x_axis} vs {slide.y_axis?.join(", ")})
                            </span>
                          </div>
                        ) : (
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                              Visual Elements
                            </span>
                            <span className="font-semibold block text-sm text-slate-500 mt-0.5">
                              Standard Text Bullet / Summary Grid
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Bullet lists */}
                      <div className="space-y-2">
                        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">
                          Analytical bullet insights
                        </span>
                        <ul className="space-y-1.5 list-disc pl-4 text-sm text-slate-400">
                          {slide.insights.map((ins, insIdx) => (
                            <li key={insIdx}>{ins}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Recommendations */}
                      {slide.recommendations && slide.recommendations.length > 0 && (
                        <div className="space-y-2 pt-2 border-t border-slate-850/30">
                          <span className="text-[10px] uppercase font-bold text-emerald-500/80 tracking-wider block">
                            Calculated Action Recommendations
                          </span>
                          <ul className="space-y-1.5 list-none text-sm text-emerald-400">
                            {slide.recommendations.map((rec, recIdx) => (
                              <li key={recIdx} className="flex items-start space-x-2">
                                <span className="mt-1.5 h-1.5 w-1.5 bg-emerald-500 rounded-full flex-shrink-0"></span>
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* End of deck controls */}
              <div className="flex items-center justify-between bg-slate-900/20 p-6 rounded-3xl border border-slate-800/80">
                <button 
                  onClick={() => {
                    if (storyboard) {
                      const newSlide = {
                        slide_id: `slide_${Date.now()}`,
                        template_id: "Executive Summary",
                        title: "Analytical Appendix Note",
                        objective: "Supplementary Metrics Summary",
                        worksheet: summary?.metadata.sheets[0].name || "",
                        insights: ["Overview data is compiled automatically.", "References are logged in ledger sheets."],
                        speaker_notes: "Speaker guide notes",
                        why_created: "Provide custom content additions",
                        priority: 3,
                        confidence: 1.0
                      };
                      setStoryboard({ ...storyboard, slides: [...storyboard.slides, newSlide] });
                    }
                  }}
                  className="bg-slate-900 hover:bg-slate-850 px-4 py-2.5 rounded-lg border border-slate-800 text-xs font-semibold inline-flex items-center space-x-1.5 transition"
                >
                  <Plus className="h-4 w-4 text-sky-400" />
                  <span>Add Custom Slide Layout</span>
                </button>

                <button 
                  onClick={compilePowerPoint}
                  className="bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-600 hover:to-indigo-600 text-white px-8 py-3.5 rounded-xl font-bold transition shadow-lg shadow-sky-500/10 inline-flex items-center space-x-2"
                >
                  <CheckCircle className="h-5 w-5" />
                  <span>Approve & Compile Storyboard</span>
                </button>
              </div>
            </motion.div>
          )}

          {/* STEP 3: Complete Success Screen */}
          {step === 3 && file && storyboard && (
            <motion.div 
              key="step3"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="max-w-2xl mx-auto bg-slate-900/40 border border-slate-800/80 p-12 rounded-3xl text-center space-y-8 backdrop-blur-sm shadow-xl"
            >
              <div className="inline-flex p-4 bg-emerald-500/10 rounded-full border border-emerald-500/30 text-emerald-400 animate-bounce">
                <CheckCircle className="h-12 w-12" />
              </div>
              
              <div>
                <h2 className="text-3xl font-extrabold text-white">PowerPoint Generated Successfully!</h2>
                <p className="text-sm text-slate-400 mt-2">
                  The presentation has been compiled and the download has started automatically.
                </p>
              </div>

              {/* Benchmarks grid */}
              <div className="grid grid-cols-2 gap-4 bg-slate-950 p-6 rounded-2xl border border-slate-850/50 text-left">
                <div>
                  <span className="text-xs font-medium text-slate-500">Processing Speed</span>
                  <span className="text-lg font-bold block text-slate-200 mt-0.5 inline-flex items-center space-x-1">
                    <Clock className="h-4 w-4 text-sky-400" />
                    <span>{(timeTakenMs / 1000).toFixed(2)} seconds</span>
                  </span>
                </div>
                
                <div>
                  <span className="text-xs font-medium text-slate-500">Slides Rendered</span>
                  <span className="text-lg font-bold block text-slate-200 mt-0.5">
                    {storyboard.slides.length} Widescreen Slides
                  </span>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button 
                  onClick={compilePowerPoint}
                  className="bg-slate-800 hover:bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl border border-slate-700 transition inline-flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4 text-sky-400" />
                  <span>Download Again</span>
                </button>

                <button 
                  onClick={handleReset}
                  className="bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-600 hover:to-indigo-600 text-white font-bold px-6 py-3 rounded-xl transition inline-flex items-center justify-center space-x-2"
                >
                  <span>Start New Project</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </main>

      {/* Footer Info */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-8 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span>&copy; 2026 DeckMate Platform. All Rights Reserved.</span>
          <div className="flex space-x-4">
            <span className="hover:text-slate-400 transition cursor-help">Stateless Privacy Policy</span>
            <span>•</span>
            <span className="hover:text-slate-400 transition cursor-help">Technical Specifications</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
