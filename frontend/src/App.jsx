import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Settings, 
  Send, 
  Database, 
  Cpu, 
  Activity,
  ChevronRight,
  Info
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const DEFAULT_ENDPOINTS = {
  openai: { name: 'GPT-4o', provider: 'openai', url: 'https://api.openai.com/v1/chat/completions' },
  anthropic: { name: 'Claude 3.5 Sonnet', provider: 'anthropic', url: 'https://api.anthropic.com/v1/messages' },
  custom: { name: 'Local Llama-3', provider: 'custom', url: 'http://localhost:11434/api/generate' }
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [trustAudit, setTrustAudit] = useState([]);
  const [selectedLlm, setSelectedLlm] = useState('openai');
  const [customUrl, setCustomUrl] = useState(DEFAULT_ENDPOINTS.openai.url);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/v1/query`, {
        query: input,
        user_id: 'dev_user',
        llm_config: {
          provider: DEFAULT_ENDPOINTS[selectedLlm].provider,
          model_name: DEFAULT_ENDPOINTS[selectedLlm].name,
          endpoint_url: customUrl
        }
      });

      const aiMessage = { 
        role: 'assistant', 
        content: response.data.final_response,
        thought: response.data.thought_process,
        tool_result: response.data.tool_result
      };

      setMessages(prev => [...prev, aiMessage]);
      setTrustAudit(response.data.trust_audit || []);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: 'Connection failed. Check if local backend is running on port 8000.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0A0A0B] text-slate-100 font-['Inter']">
      
      {/* Sidebar: Trust Analytics */}
      <aside className="w-80 border-r border-white/5 bg-[#0F0F12] p-6 flex flex-col gap-6">
        <div className="flex items-center gap-3 mb-4">
          <ShieldCheck className="w-8 h-8 text-indigo-500" />
          <h1 className="text-xl font-bold tracking-tight">DATA PLANE</h1>
        </div>

        <div className="flex-1 overflow-y-auto space-y-6">
          <div>
            <h3 className="text-xs font-semibold uppercase text-slate-500 tracking-wider mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" /> Real-time Trust Audit
            </h3>
            <div className="space-y-3">
              {trustAudit.length > 0 ? trustAudit.map((item, i) => (
                <div key={i} className="p-3 rounded-lg bg-white/5 border border-white/5 text-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-indigo-400 font-mono">Source {i+1}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${item.trust_score > 0.7 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                      {(item.trust_score * 100).toFixed(0)}% TRUST
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs italic">
                    {item.classification.join(', ')} - Analyzed via L3 Transformation
                  </p>
                </div>
              )) : (
                <div className="text-slate-600 text-sm italic">No data processed.</div>
              )}
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-white/5">
          <div className="flex items-center gap-2 text-slate-400 text-xs">
            <Database className="w-3 h-3" /> Hardware-Isolated RAG Layer
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col items-center justify-between p-8 relative overflow-hidden">
        {/* Decorative Gradients */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

        {/* Top Header */}
        <header className="w-full max-w-4xl flex justify-between items-center z-10">
          <div className="text-slate-400 text-sm flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/5">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            Gateway Status: <span className="text-slate-200">Active - HMAC Signed</span>
          </div>
          
          <div className="flex items-center gap-4">
             <div className="flex flex-col items-end">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Active Model</span>
                <span className="text-sm font-medium text-indigo-300">{DEFAULT_ENDPOINTS[selectedLlm].name}</span>
             </div>
             <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Cpu className="w-5 h-5" />
             </div>
          </div>
        </header>

        {/* Messages */}
        <section className="flex-1 w-full max-w-4xl overflow-y-auto space-y-8 py-12 scrollbar-none z-10">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
              <ShieldCheck className="w-16 h-16 text-indigo-500/20" />
              <h2 className="text-2xl font-light text-slate-300">Secure Orchestration Hub</h2>
              <p className="text-slate-500 max-w-md">Multi-channel input isolation and capability-based tool execution in a hard-isolated data plane.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] space-y-4`}>
                <div className={`p-5 rounded-2xl ${m.role === 'user' ? 'bg-indigo-600' : 'bg-[#16161A] border border-white/5 shadow-2xl'}`}>
                  <p className="text-sm leading-relaxed">{m.content}</p>
                  {m.tool_result && (
                     <div className="mt-4 pt-4 border-t border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                           <Database className="w-3 h-3 text-indigo-400" />
                           <span className="text-[10px] uppercase font-bold text-slate-500">Tool Execution Result</span>
                        </div>
                        <pre className="text-xs bg-black/40 p-3 rounded-lg text-emerald-400 font-mono overflow-x-auto">
                           {JSON.stringify(m.tool_result.data, null, 2)}
                        </pre>
                     </div>
                  )}
                </div>
                {m.thought && (
                  <div className="flex items-start gap-2 px-2">
                    <ChevronRight className="w-3 h-3 text-indigo-500 mt-1" />
                    <p className="text-[11px] text-slate-500 italic font-mono">{m.thought}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </section>

        {/* Input & Control Panel */}
        <footer className="w-full max-w-4xl z-10">
           <div className="bg-[#16161A]/80 backdrop-blur-3xl border border-white/5 p-4 rounded-3xl shadow-2xl space-y-4">
              <div className="flex gap-4">
                 <input 
                    className="flex-1 bg-transparent border-none outline-none text-slate-200 placeholder:text-slate-600 px-4"
                    placeholder="Type to securely query LLM..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                 />
                 <button 
                    onClick={handleSend}
                    disabled={loading}
                    className="p-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-2xl transition-all shadow-lg shadow-indigo-600/20"
                 >
                    <Send className={`w-5 h-5 ${loading && 'animate-spin'}`} />
                 </button>
              </div>
              <div className="flex items-center justify-between pt-4 border-t border-white/5">
                 <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                       <span className="text-[10px] text-slate-500 uppercase font-black">Model Selection:</span>
                       <select 
                          className="bg-transparent text-xs text-indigo-400 outline-none cursor-pointer"
                          value={selectedLlm}
                          onChange={(e) => {
                             setSelectedLlm(e.target.value);
                             setCustomUrl(DEFAULT_ENDPOINTS[e.target.value].url);
                          }}
                       >
                          <option value="openai">GPT-4o (OpenAI)</option>
                          <option value="anthropic">Claude 3.5 (Anthropic)</option>
                          <option value="custom">Local Llama-3 (Ollama)</option>
                       </select>
                    </div>
                    
                    <div className="flex items-center gap-2">
                       <ShieldAlert className="w-3 h-3 text-amber-500" />
                       <span className="text-[10px] text-slate-500 uppercase font-black">Isolation Level:</span>
                       <span className="text-xs text-slate-400">HARD (L3 Transform)</span>
                    </div>
                 </div>

                 <div className="flex items-center gap-2 bg-indigo-500/10 px-3 py-1.5 rounded-xl border border-indigo-500/20">
                    <Settings className="w-3 h-3 text-indigo-400" />
                    <input 
                       className="bg-transparent text-[10px] text-indigo-300 font-mono outline-none w-48"
                       value={customUrl}
                       onChange={(e) => setCustomUrl(e.target.value)}
                       placeholder="Endpoint URL..."
                    />
                 </div>
              </div>
           </div>
        </footer>

      </main>
    </div>
  );
}
