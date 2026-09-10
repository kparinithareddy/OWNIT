import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot,
  Send,
  User,
  Sparkles,
  Trash2,
  RefreshCw,
  Cpu,
  Info,
  ShieldCheck,
  FileText,
  Wrench,
  Layers,
  AlertCircle,
  ExternalLink,
  Building,
  Globe
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { aiApi } from '../../services/api';
import './ProductAIChatWidget.css';

function renderSourceIcon(sourceType) {
  switch (sourceType) {
    case 'user_document': return FileText;
    case 'official_manufacturer': return Building;
    case 'reliable_external': return Globe;
    default: return Info;
  }
}


const DEFAULT_SUGGESTED_PROMPTS = [
  "What is covered under my warranty?",
  "How should I clean and maintain this item?",
  "What are the explicit warranty exclusions?",
  "Draft a warranty claim message for customer support"
];

export default function ProductAIChatWidget({ product, warranties = [], documents = [], maintenanceRecords = [] }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(true);
  const [aiStatus, setAiStatus] = useState(null);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAiStatus = useCallback(async () => {
    try {
      const statusRes = await aiApi.getStatus();
      setAiStatus(statusRes);
    } catch (err) {
      console.warn('Could not load AI status:', err);
      setAiStatus({ isAvailable: false, provider: 'Ollama', message: 'Local Ollama is offline' });
    }
  }, []);

  const loadChatHistory = useCallback(async () => {
    if (!product?.id) return;
    try {
      setFetchingHistory(true);
      setError(null);
      const res = await aiApi.getChatHistory(product.id);
      if (res.messages && res.messages.length > 0) {
        setMessages(res.messages);
      } else {
        // Initial welcome message
        setMessages([
          {
            id: 'welcome-0',
            role: 'assistant',
            content: `Hello! I am your OWNIT Product Assistant for **${product.brand} ${product.name}**.\n\nI have instant access to your **${warranties.length} warranty component(s)**, **${documents.length} attached document(s)**, and maintenance records.\n\nAsk me anything about coverage, cleaning intervals, claim procedures, or troubleshooting!`,
            sources: [`${product.brand} ${product.name} Dossier`],
            createdAt: new Date().toISOString()
          }
        ]);
      }
    } catch (err) {
      console.error('Error fetching chat history:', err);
      setError('Could not retrieve chat history.');
    } finally {
      setFetchingHistory(false);
    }
  }, [product?.id, product?.brand, product?.name, warranties.length, documents.length]);

  useEffect(() => {
    loadAiStatus();
    loadChatHistory();
  }, [loadAiStatus, loadChatHistory]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    const tempUserMsg = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: text,
      sources: [],
      createdAt: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const res = await aiApi.sendMessage({
        productId: product.id,
        message: text
      });

      // Replace messages or append
      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUserMsg.id);
        return [...withoutTemp, res.userMessage, res.assistantMessage];
      });
    } catch (err) {
      console.error('Chat error:', err);
      const errMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ ${err.message || 'Could not reach local AI service. Please ensure Ollama is running.'}`,
        sources: ['Connection Error'],
        createdAt: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm(`Clear chat conversation for "${product.name}"?`)) return;
    try {
      await aiApi.clearChatHistory(product.id);
      setMessages([
        {
          id: `welcome-${Date.now()}`,
          role: 'assistant',
          content: `Conversation cleared. How can I help you with your **${product.brand} ${product.name}** today?`,
          sources: [`${product.brand} ${product.name} Dossier`],
          createdAt: new Date().toISOString()
        }
      ]);
    } catch (err) {
      alert(`Could not clear history: ${err.message}`);
    }
  };

  return (
    <Card className="product-ai-chat-card" padding="none">
      {/* Top Header */}
      <div className="product-ai-header">
        <div className="ai-header-left">
          <div className="ai-header-avatar">
            <Bot size={20} />
          </div>
          <div>
            <div className="ai-header-title-row">
              <h4 className="ai-header-title">{product.name} AI Assistant</h4>
              {aiStatus && (
                <Badge variant={aiStatus.isAvailable ? 'active' : 'warning'} size="sm" dot>
                  {aiStatus.isAvailable ? `Ollama (${aiStatus.configuredModel})` : 'Offline Fallback'}
                </Badge>
              )}
            </div>
            <p className="ai-header-desc">
              Context-anchored to {warranties.length} warranties, {documents.length} documents, and maintenance logs
            </p>
          </div>
        </div>

        <div className="ai-header-actions">
          <Button
            variant="ghost"
            size="sm"
            icon={Trash2}
            onClick={handleClearHistory}
            title="Clear Chat History"
          >
            Clear History
          </Button>
        </div>
      </div>

      {/* Main Chat Messages Container */}
      <div className="product-ai-messages-wrap">
        {fetchingHistory ? (
          <div className="chat-loading-box">
            <RefreshCw size={20} className="spinning" />
            <span>Loading product conversation...</span>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`chat-bubble-row ${isUser ? 'chat-row-user' : 'chat-row-ai'}`}
              >
                <div className={`chat-avatar ${isUser ? 'avatar-user' : 'avatar-ai'}`}>
                  {isUser ? <User size={16} /> : <Bot size={16} />}
                </div>

                <div className="chat-bubble-content">
                  <div className="chat-bubble-header">
                    <span className="chat-sender-name">
                      {isUser ? 'You' : `${product.brand} Assistant`}
                    </span>
                    <span className="chat-time">
                      {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <div className="chat-text" style={{ whiteSpace: 'pre-line' }}>
                    {msg.content}
                  </div>

                  {/* Sourced References Pills / Structured Badges */}
                  {!isUser && ((msg.sourceReferences && msg.sourceReferences.length > 0) || (msg.sources && msg.sources.length > 0)) && (
                    <div className="chat-sources-row">
                      <span className="sources-label">
                        <ShieldCheck size={12} className="shield-icon" /> Sourced via:
                      </span>
                      {msg.sourceReferences && msg.sourceReferences.length > 0 ? (
                        msg.sourceReferences.map((refItem, rIdx) => {
                          const IconComp = renderSourceIcon(refItem.sourceType);
                          const isOem = refItem.sourceType === 'official_manufacturer';
                          const isDoc = refItem.sourceType === 'user_document';
                          const isExt = refItem.sourceType === 'reliable_external';
                          const tierClass = isDoc
                            ? 'source-ref-user-doc'
                            : isOem
                            ? 'source-ref-oem'
                            : isExt
                            ? 'source-ref-ext'
                            : 'source-ref-general';

                          return refItem.url ? (
                            <a
                              key={rIdx}
                              href={refItem.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`source-ref-badge ${tierClass}`}
                              title={refItem.details || refItem.title}
                            >
                              <IconComp size={11} className="source-type-icon" />
                              <span className="source-ref-title">{refItem.title}</span>
                              {refItem.domain && (
                                <span className="source-ref-domain">({refItem.domain})</span>
                              )}
                              <ExternalLink size={10} className="external-link-icon" />
                            </a>
                          ) : (
                            <span
                              key={rIdx}
                              className={`source-ref-badge ${tierClass}`}
                              title={refItem.details || refItem.title}
                            >
                              <IconComp size={11} className="source-type-icon" />
                              <span className="source-ref-title">{refItem.title}</span>
                              {refItem.domain && (
                                <span className="source-ref-domain">({refItem.domain})</span>
                              )}
                            </span>
                          );
                        })
                      ) : (
                        msg.sources.map((src, sIdx) => (
                          <span key={sIdx} className="source-pill">
                            {src}
                          </span>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {loading && (
          <div className="chat-bubble-row chat-row-ai">
            <div className="chat-avatar avatar-ai">
              <Bot size={16} />
            </div>
            <div className="chat-bubble-content">
              <div className="chat-typing-indicator">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="product-ai-quick-prompts">
        <span className="quick-prompts-label">
          <Sparkles size={12} /> Suggested Queries:
        </span>
        <div className="quick-prompts-row">
          {DEFAULT_SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              className="quick-prompt-btn"
              onClick={() => handleSendMessage(prompt)}
              disabled={loading}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Input Bar */}
      <div className="product-ai-input-bar">
        <input
          type="text"
          placeholder={`Ask about ${product.name} warranty coverage, cleaning, or claim steps...`}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          disabled={loading}
          className="product-ai-input"
        />
        <Button
          variant="primary"
          icon={Send}
          onClick={() => handleSendMessage()}
          disabled={!inputMessage.trim() || loading}
        >
          Send
        </Button>
      </div>
    </Card>
  );
}
