import { useRef, useState, useCallback, useEffect } from "react";
import { Excalidraw, convertToExcalidrawElements } from "@excalidraw/excalidraw";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import "@excalidraw/excalidraw/index.css";
import { transcribeAudio, generateDiagram, voiceDiagram } from "./api";
import "./App.css";

type Status = "idle" | "recording" | "processing";
interface HistoryEntry {
  label: string;
  explanation: string;
  fullPrompt: string;
}

interface SavedDiagram {
  id: string;
  name: string;
  elements: any[];
  history: HistoryEntry[];
  createdAt: number;
}

const DEFAULT: any[] = [
  {
    type: "text", x: 200, y: 180,
    text: 'Press 🎤 and say something\ne.g. "Design a URL shortener"',
    fontSize: 24, textAlign: "center", strokeColor: "#a6adc8",
  },
];

const getApiHistory = (history: HistoryEntry[]) => {
  return history
    .slice(0, 5)
    .reverse()
    .flatMap((item) => [
      { role: "user", content: item.fullPrompt },
      { role: "assistant", content: item.explanation },
    ]);
};

export default function App() {
  const excRef = useRef<ExcalidrawImperativeAPI>(null);
  const mrRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [status, setStatus] = useState<Status>("idle");
  const [textPrompt, setTextPrompt] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [captions, setCaptions] = useState("");

  // Persistent Storage State
  const [currentDiagramId, setCurrentDiagramId] = useState<string | null>(null);
  const [diagramName, setDiagramName] = useState("Untitled");
  const [isEditingName, setIsEditingName] = useState(false);
  const [savedDiagrams, setSavedDiagrams] = useState<SavedDiagram[]>([]);
  const [showFolderDropdown, setShowFolderDropdown] = useState(false);

  // Load Saved Diagrams on Mount
  useEffect(() => {
    const stored = localStorage.getItem("voicedraw_diagrams");
    if (stored) {
      try {
        setSavedDiagrams(JSON.parse(stored));
      } catch (e) {
        console.error("Error loading saved diagrams:", e);
      }
    }
  }, []);

  const ready = useCallback((api: ExcalidrawImperativeAPI) => {
    excRef.current = api;
    try {
      api.updateScene({ elements: convertToExcalidrawElements(DEFAULT) });
    } catch (err) {
      console.error("Error setting default scene:", err);
    }
  }, []);

  const render = useCallback((elements: any[]) => {
    if (!excRef.current) return;
    try {
      // Normalize coordinates for drawing arrows/lines (relative to [x, y])
      const normalized = elements.map((el) => {
        if ((el.type === "arrow" || el.type === "line") && el.points && el.points.length > 0) {
          const [firstX, firstY] = el.points[0];
          return {
            ...el,
            x: firstX,
            y: firstY,
            points: el.points.map(([px, py]: [number, number]) => [px - firstX, py - firstY]),
          };
        }
        return el;
      });
      const converted = convertToExcalidrawElements(normalized, { regenerateIds: false });
      excRef.current.updateScene({ elements: converted });
    } catch (err) {
      console.error("Error converting/rendering scene:", err);
    }
  }, []);

  const currentElements = (): any[] => {
    return (excRef.current?.getSceneElements() ?? []) as any[];
  };

  // ── Database Storage Operations ──────────────────────────────────────

  const saveDiagram = useCallback((nameToSave = diagramName, idToSave = currentDiagramId, historyToSave = history) => {
    if (!excRef.current) return;
    const elements = excRef.current.getSceneElements();
    if (!elements || elements.length === 0) return;

    const stored = localStorage.getItem("voicedraw_diagrams");
    let list: SavedDiagram[] = [];
    if (stored) {
      try { list = JSON.parse(stored); } catch {}
    }

    let activeId = idToSave;
    if (!activeId) {
      activeId = Date.now().toString();
      setCurrentDiagramId(activeId);
    }

    const existingIndex = list.findIndex(d => d.id === activeId);
    const diagramData: SavedDiagram = {
      id: activeId!,
      name: nameToSave,
      elements: elements as any[],
      history: historyToSave,
      createdAt: Date.now()
    };

    if (existingIndex > -1) {
      list[existingIndex] = diagramData;
    } else {
      list.push(diagramData);
    }

    localStorage.setItem("voicedraw_diagrams", JSON.stringify(list));
    setSavedDiagrams(list);
  }, [diagramName, currentDiagramId, history]);

  const loadSavedDiagram = (diagram: SavedDiagram) => {
    setCurrentDiagramId(diagram.id);
    setDiagramName(diagram.name);
    setHistory(diagram.history || []);
    setCaptions("");
    if (excRef.current) {
      try {
        excRef.current.updateScene({ elements: convertToExcalidrawElements(diagram.elements) });
      } catch (err) {
        console.error("Error loading elements:", err);
      }
    }
    setShowFolderDropdown(false);
  };

  const deleteSavedDiagram = (idToDelete: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent loading on item click
    const stored = localStorage.getItem("voicedraw_diagrams");
    let list: SavedDiagram[] = [];
    if (stored) {
      try { list = JSON.parse(stored); } catch {}
    }
    const filtered = list.filter(d => d.id !== idToDelete);
    localStorage.setItem("voicedraw_diagrams", JSON.stringify(filtered));
    setSavedDiagrams(filtered);
    
    if (currentDiagramId === idToDelete) {
      handleNewDiagram();
    }
  };

  const handleRenameComplete = (newName: string) => {
    setIsEditingName(false);
    const trimmed = newName.trim();
    if (!trimmed) return;
    setDiagramName(trimmed);
    saveDiagram(trimmed, currentDiagramId, history);
  };

  // ── Voice ────────────────────────────────────────────────────────────

  const startRecord = useCallback(async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      const r = new MediaRecorder(s, { mimeType: "audio/webm" });
      mrRef.current = r;
      chunksRef.current = [];
      r.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      r.onstop = async () => {
        s.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) { setStatus("idle"); return; }

        setStatus("processing");
        try {
          const res = await voiceDiagram(blob, currentElements(), getApiHistory(history));
          render(res.scene.elements);
          const promptText = res.prompt || "Voice Command";
          const newHistory = [{ label: promptText, explanation: res.explanation || "", fullPrompt: promptText }, ...history];
          setHistory(newHistory);
          setCaptions(promptText);
          saveDiagram(diagramName, currentDiagramId, newHistory);
        } catch {
          try {
            const text = await transcribeAudio(blob);
            setTextPrompt(text);
            const res = await generateDiagram(text, currentElements(), getApiHistory(history));
            render(res.scene.elements);
            const newHistory = [{ label: text, explanation: res.explanation || "", fullPrompt: text }, ...history];
            setHistory(newHistory);
            setCaptions(text);
            saveDiagram(diagramName, currentDiagramId, newHistory);
          } catch { /* ignore */ }
        }
        setStatus("idle");
      };
      r.start();
      setStatus("recording");
    } catch { setStatus("idle"); }
  }, [render, history, diagramName, currentDiagramId, saveDiagram]);

  const stopRecord = useCallback(() => { mrRef.current?.stop(); }, []);

  // ── Text / Suggestions ───────────────────────────────────────────────

  const handleSubmit = useCallback(async () => {
    const p = textPrompt.trim();
    if (!p) return;
    setStatus("processing");
    try {
      const res = await generateDiagram(p, currentElements(), getApiHistory(history));
      render(res.scene.elements);
      const newHistory = [{ label: p, explanation: res.explanation || "", fullPrompt: p }, ...history];
      setHistory(newHistory);
      setCaptions(p);
      setTextPrompt("");
      saveDiagram(diagramName, currentDiagramId, newHistory);
    } catch { /* ignore */ }
    setStatus("idle");
  }, [textPrompt, render, history, diagramName, currentDiagramId, saveDiagram]);

  const handleSuggestion = useCallback(async (suggestion: string) => {
    setStatus("processing");
    try {
      const res = await generateDiagram(suggestion, currentElements(), getApiHistory(history));
      render(res.scene.elements);
      const newHistory = [{ label: suggestion, explanation: res.explanation || "", fullPrompt: suggestion }, ...history];
      setHistory(newHistory);
      setCaptions(suggestion);
      saveDiagram(diagramName, currentDiagramId, newHistory);
    } catch { /* ignore */ }
    setStatus("idle");
  }, [render, history, diagramName, currentDiagramId, saveDiagram]);

  // ── Header Actions ───────────────────────────────────────────────────

  const handleNewDiagram = useCallback(() => {
    if (excRef.current) {
      try {
        excRef.current.updateScene({ elements: convertToExcalidrawElements(DEFAULT) });
        setHistory([]);
        setCaptions("");
        setDiagramName("Untitled");
        setCurrentDiagramId(null);
      } catch (err) {
        console.error("Error resetting canvas:", err);
      }
    }
  }, []);

  // ── Keyboard ─────────────────────────────────────────────────────────

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === " " && e.target === document.body) {
        e.preventDefault();
        if (status === "recording") stopRecord();
        else startRecord();
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [status, startRecord, stopRecord]);

  // ── Render ───────────────────────────────────────────────────────────

  const defaultSuggestions = [
    "design a URL shortener",
    "design WhatsApp",
    "design YouTube",
  ];

  return (
    <div className="app-container">
      {/* Top Header Bar */}
      <header className="top-header">
        <div className="header-left">
          <div className="logo-section">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="logo-icon">
              <line x1="12" y1="12" x2="8" y2="7" />
              <line x1="12" y1="12" x2="16" y2="7" />
              <line x1="12" y1="12" x2="7" y2="12" />
              <line x1="12" y1="12" x2="17" y2="12" />
              <line x1="12" y1="12" x2="8" y2="17" />
              <line x1="12" y1="12" x2="16" y2="17" />
              <circle cx="12" cy="12" r="2.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="8" cy="7" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="16" cy="7" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="7" cy="12" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="17" cy="12" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="8" cy="17" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
              <circle cx="16" cy="17" r="1.5" fill="#1e1e1e" stroke="#3b82f6" strokeWidth="2.5" />
            </svg>
            <span className="logo-text">VoiceDraw</span>
          </div>

          <button 
            className={`action-btn sidebar-toggle ${showSidebar ? 'active' : ''}`}
            onClick={() => setShowSidebar(!showSidebar)}
            title="Show AI panel"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <path d="M9 3v18" />
            </svg>
          </button>

          <div className="folder-action-wrapper" style={{ position: "relative" }}>
            <button 
              className={`action-btn ${showFolderDropdown ? 'active' : ''}`}
              onClick={() => setShowFolderDropdown(!showFolderDropdown)}
              title="Open folder"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
              </svg>
            </button>

            {/* Folder Dropdown */}
            {showFolderDropdown && (
              <div className="folder-dropdown">
                <div className="dropdown-header">saved diagrams</div>
                <div className="dropdown-list">
                  {savedDiagrams.length === 0 ? (
                    <div className="dropdown-empty">no saved diagrams</div>
                  ) : (
                    savedDiagrams.map((d) => (
                      <div className="dropdown-item" key={d.id} onClick={() => loadSavedDiagram(d)}>
                        <span className="diagram-item-name">{d.name}</span>
                        <button className="delete-btn" onClick={(e) => deleteSavedDiagram(d.id, e)} title="Delete diagram">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <button className="action-btn" onClick={handleNewDiagram} title="New diagram">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14" />
              <path d="M12 5v14" />
            </svg>
          </button>
        </div>

        <div className="header-center">
          {isEditingName ? (
            <input
              className="diagram-title-input"
              defaultValue={diagramName}
              onBlur={(e) => handleRenameComplete(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleRenameComplete(e.currentTarget.value);
                }
              }}
              autoFocus
            />
          ) : (
            <span className="diagram-title" onClick={() => setIsEditingName(true)} title="Click to rename">
              {diagramName}
            </span>
          )}
        </div>

        <div className="header-right">
          <button 
            className="action-btn theme-toggle" 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2" />
                <path d="M12 20v2" />
                <path d="M4.93 4.93l1.41 1.41" />
                <path d="M17.66 17.66l1.41 1.41" />
                <path d="M2 12h2" />
                <path d="M20 12h2" />
                <path d="M6.34 17.66l-1.41 1.41" />
                <path d="M19.07 4.93l-1.41 1.41" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
              </svg>
            )}
          </button>

          <div className="profile-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="workspace">
        {/* Collapsible Sidebar */}
        <div className={`sidebar ${showSidebar ? "open" : "collapsed"}`}>
          <header className="sidebar-header">
            <h1 className="title">diagram assistant</h1>
            <p className="subtitle">modify & refine your design</p>
          </header>

          <div className="terminal-prompt">
            <span className="prompt-char">&gt;</span>
            <input
              value={textPrompt}
              onChange={(e) => setTextPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="type a prompt"
              disabled={status === "processing"}
            />
          </div>

          <div className="recent-commands-section">
            <h2 className="section-title">recent commands</h2>
            <div className="commands-list">
              {history.length === 0 ? (
                defaultSuggestions.map((suggestion, idx) => (
                  <div
                    className="command-item suggestion"
                    key={idx}
                    onClick={() => handleSuggestion(suggestion)}
                  >
                    <span className="command-arrow">↳</span>
                    <span className="command-text">{suggestion}</span>
                  </div>
                ))
              ) : (
                history.map((item, idx) => (
                  <div className="command-item-container" key={idx}>
                    <div
                      className="command-item history-cmd"
                      onClick={() => handleSuggestion(item.fullPrompt)}
                    >
                      <span className="command-arrow">↳</span>
                      <span className="command-text">{item.label}</span>
                    </div>
                    {item.explanation && (
                      <div className="command-explanation">
                        {item.explanation}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="canvas-container">
          <Excalidraw excalidrawAPI={ready} initialData={{ elements: DEFAULT }} theme={theme} />

          {/* Floating Voice Captions Bar */}
          <div className="floating-voice-bar">
            <div className="voice-bar-content">
              <div className={`audio-visualizer-mini ${status}`}>
                <div className="bar" />
                <div className="bar" />
                <div className="bar" />
                <div className="bar" />
                <div className="bar" />
              </div>

              <p className="caption-text">
                {status === "idle" && (captions || "press space or tap to speak")}
                {status === "recording" && "listening..."}
                {status === "processing" && "generating diagram..."}
              </p>

              <button
                className={`mic-trigger ${status}`}
                onClick={() => status === "recording" ? stopRecord() : startRecord()}
                disabled={status === "processing"}
                aria-label="Toggle voice recording"
              >
                {status === "processing" ? (
                  <svg className="spinner-mini" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="8" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="22" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
