import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, X, RotateCcw, Loader2, Bot, CornerDownLeft } from 'lucide-react';
import { api } from '../lib/api';

interface Message {
  role: 'user' | 'model';
  content: string;
}

interface FeedbackChatbotProps {
  academicSessionId?: number | string;
}

export default function FeedbackChatbot({ academicSessionId = 9 }: FeedbackChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount or when opening
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadHistory();
    }
  }, [isOpen]);

  // Auto scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    setErrorMsg('');
    try {
      const response = await api.post('/chat/history');
      if (response.data?.history) {
        setMessages(response.data.history);
      }
    } catch (err: any) {
      console.error("Error loading chat history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setErrorMsg('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await api.post('/chat', {
        message: userMessage,
        academic_session: Number(academicSessionId) || 9
      });

      if (response.data?.response) {
        setMessages(prev => [...prev, { role: 'model', content: response.data.response }]);
      } else {
        throw new Error("Empty response");
      }
    } catch (err: any) {
      console.error("Error sending message:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to communicate with chatbot";
      setErrorMsg(detail);
      setMessages(prev => [
        ...prev,
        { role: 'model', content: `⚠️ **Error**: {detail}. Please check your connection or environment.` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetHistory = async () => {
    if (!window.confirm("Are you sure you want to clear your feedback chat history?")) return;
    setLoading(true);
    try {
      await api.post('/chat/reset');
      setMessages([]);
      setErrorMsg('');
    } catch (err: any) {
      console.error("Error resetting chat history:", err);
      alert("Failed to reset history: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // Modern parsing function to render Markdown Tables, Bold text, lists, and headers in UI
  const parseMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let currentTable: string[][] = [];
    let isTable = false;
    let listItems: string[] = [];
    let isList = false;

    const flushList = (key: string) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-${key}`} className="list-disc pl-5 space-y-1 my-2 text-slate-700">
            {listItems.map((item, idx) => (
              <li key={idx} dangerouslySetInnerHTML={{ __html: formatInline(item) }} />
            ))}
          </ul>
        );
        listItems = [];
        isList = false;
      }
    };

    const flushTable = (key: string) => {
      if (currentTable.length > 0) {
        const rows = currentTable.filter(row => !row.every(cell => cell.trim().match(/^:?-+:?$/)));
        if (rows.length > 0) {
          const headers = rows[0];
          const body = rows.slice(1);
          elements.push(
            <div key={`table-${key}`} className="overflow-x-auto my-3 border border-slate-200 rounded-xl shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-[11px] leading-normal font-sans">
                <thead className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider">
                  <tr>
                    {headers.map((h, i) => (
                      <th key={i} className="px-3 py-2 text-left border-r last:border-r-0 border-slate-200">{h.trim()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white text-slate-600">
                  {body.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50/50 transition-colors">
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="px-3 py-2 border-r last:border-r-0 border-slate-100 font-medium" dangerouslySetInnerHTML={{ __html: formatInline(cell) }} />
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        currentTable = [];
        isTable = false;
      }
    };

    const formatInline = (str: string) => {
      let formatted = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
      formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-slate-100 text-indigo-600 px-1.5 py-0.5 rounded font-mono text-[10px]">$1</code>');
      return formatted;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        flushList(`before-table-${i}`);
        isTable = true;
        const cells = line.split('|').slice(1, -1);
        currentTable.push(cells);
        continue;
      } else {
        if (isTable) flushTable(`table-end-${i}`);
      }

      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        isList = true;
        listItems.push(trimmed.slice(2));
        continue;
      } else {
        if (isList) flushList(`list-end-${i}`);
      }

      if (trimmed.startsWith('### ')) {
        elements.push(
          <h4 key={i} className="text-xs font-bold text-slate-800 mt-3 mb-1 uppercase tracking-wide" dangerouslySetInnerHTML={{ __html: formatInline(trimmed.slice(4)) }} />
        );
        continue;
      }
      if (trimmed.startsWith('## ')) {
        elements.push(
          <h3 key={i} className="text-sm font-extrabold text-slate-900 mt-3.5 mb-1.5" dangerouslySetInnerHTML={{ __html: formatInline(trimmed.slice(3)) }} />
        );
        continue;
      }
      if (trimmed.startsWith('# ')) {
        elements.push(
          <h2 key={i} className="text-base font-black text-indigo-700 mt-4 mb-2 pb-1 border-b border-slate-100" dangerouslySetInnerHTML={{ __html: formatInline(trimmed.slice(2)) }} />
        );
        continue;
      }

      if (trimmed) {
        elements.push(
          <p key={i} className="leading-relaxed my-1" dangerouslySetInnerHTML={{ __html: formatInline(line) }} />
        );
      } else {
        elements.push(<div key={i} className="h-1.5" />);
      }
    }

    flushList('final');
    flushTable('final');

    return elements;
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 flex items-center justify-center w-14 h-14 bg-gradient-to-tr from-indigo-600 to-violet-600 text-white rounded-full shadow-[0_8px_30px_rgb(79,70,229,0.4)] hover:shadow-[0_8px_30px_rgb(79,70,229,0.7)] hover:scale-110 hover:-translate-y-0.5 active:scale-95 transition-all duration-300 group"
        title="Open Feedback 360 AI Assistant"
      >
        {isOpen ? <X className="w-6 h-6" /> : (
          <div className="relative">
            <MessageSquare className="w-6 h-6 group-hover:rotate-6 transition-transform" />
            <span className="absolute -top-1.5 -right-1.5 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
        )}
      </button>

      {/* Expandable Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-[420px] max-w-[calc(100vw-2rem)] h-[620px] max-h-[calc(100vh-8rem)] z-50 bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.12)] border border-slate-100 flex flex-col overflow-hidden animate-slide-up duration-300">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white px-4 py-3.5 flex items-center justify-between border-b border-indigo-100/10">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 bg-white/10 rounded-lg backdrop-blur-sm">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-wide">Appraisal Assistant</h3>
                <span className="text-[10px] text-indigo-100 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
                  Active session feedback helper
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleResetHistory}
                disabled={loading || historyLoading || messages.length === 0}
                className="p-1.5 hover:bg-white/10 rounded-lg text-indigo-100 hover:text-white transition-colors disabled:opacity-40"
                title="Reset conversation history"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/10 rounded-lg text-indigo-100 hover:text-white transition-colors"
                title="Close assistant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50 scroll-smooth">
            {messages.length === 0 && !historyLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
                <div className="p-3.5 bg-indigo-50 text-indigo-600 rounded-2xl animate-bounce">
                  <Bot className="w-7 h-7" />
                </div>
                <h4 className="font-extrabold text-slate-800 text-sm">360° Feedback AI Copilot</h4>
                <p className="text-xs text-slate-500 max-w-[280px] leading-relaxed">
                  Ask me about your Annexures, final scores, appraisal status, department evaluations, or pending reviews!
                </p>
                <div className="w-full max-w-[280px] flex flex-col gap-2 pt-2 text-[11px]">
                  <button 
                    onClick={() => { setInputValue("What is my final score?"); }}
                    className="px-3 py-1.5 bg-white border border-slate-100 hover:border-indigo-300 hover:bg-indigo-50/20 text-slate-600 hover:text-indigo-600 text-left rounded-xl shadow-sm transition-all"
                  >
                    "What is my final score?"
                  </button>
                  <button 
                    onClick={() => { setInputValue("Show my Annexure I details."); }}
                    className="px-3 py-1.5 bg-white border border-slate-100 hover:border-indigo-300 hover:bg-indigo-50/20 text-slate-600 hover:text-indigo-600 text-left rounded-xl shadow-sm transition-all"
                  >
                    "Show my Annexure I details."
                  </button>
                  <button 
                    onClick={() => { setInputValue("Have I submitted my appraisal?"); }}
                    className="px-3 py-1.5 bg-white border border-slate-100 hover:border-indigo-300 hover:bg-indigo-50/20 text-slate-600 hover:text-indigo-600 text-left rounded-xl shadow-sm transition-all"
                  >
                    "Have I submitted my appraisal?"
                  </button>
                </div>
              </div>
            )}

            {historyLoading && (
              <div className="flex flex-col items-center justify-center h-full space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
                <span className="text-[11px] text-slate-400">Loading conversation history...</span>
              </div>
            )}

            {messages.map((msg, index) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={index}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
                >
                  <div
                    className={`rounded-2xl px-3.5 py-2 text-xs shadow-sm max-w-[85%] leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white rounded-tr-none'
                        : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none font-sans'
                    }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                    ) : (
                      <div className="space-y-1">
                        {parseMarkdown(msg.content)}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start animate-pulse">
                <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Panel */}
          <form onSubmit={handleSendMessage} className="p-3 bg-white border-t border-slate-100 flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask anything about 360 feedback..."
              disabled={loading || historyLoading}
              className="flex-1 border border-slate-200 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-slate-50/50 hover:bg-slate-50 focus:bg-white transition-all placeholder-slate-400 disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || loading || historyLoading}
              className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white rounded-xl shadow-md hover:shadow-lg disabled:opacity-40 hover:scale-105 active:scale-95 transition-all duration-150"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
