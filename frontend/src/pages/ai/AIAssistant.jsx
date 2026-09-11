import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Bot,
  Send,
  User,
  Sparkles,
  Plus,
  Trash2,
  Cpu,
  Globe,
  Package,
  ShieldCheck,
  FileText,
  Building,
  ArrowRight,
  ExternalLink,
  Layers,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  MessageSquare
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import { useLanguage } from '../../i18n/LanguageContext';
import { aiApi, productsApi } from '../../services/api';
import './AIAssistant.css';

function renderSourceIcon(sourceType) {
  switch (sourceType) {
    case 'user_document': return FileText;
    case 'official_manufacturer': return Building;
    case 'reliable_external': return Globe;
    default: return HelpCircle;
  }
}

function formatProductName(brand, name) {
  if (!name) return brand || 'Product';
  if (!brand) return name;
  if (name.toLowerCase().startsWith(brand.toLowerCase())) {
    return name;
  }
  return `${brand} ${name}`;
}


export default function AIAssistant() {
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);

  // Active mode settings
  const [contextMode, setContextMode] = useState('global'); // 'global' | 'product'
  const [selectedProductId, setSelectedProductId] = useState('');

  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // 1. Initial Data Load
  const fetchInitial = useCallback(async () => {
    try {
      setLoadingInitial(true);
      const [prodList, convListRes, statusRes] = await Promise.all([
        productsApi.list().catch(() => []),
        aiApi.listConversations().catch(() => ({ conversations: [], total: 0 })),
        aiApi.getStatus().catch(() => ({ isAvailable: false, configuredModel: 'llama3.2', provider: 'Ollama' }))
      ]);

      setProducts(prodList || []);
      setAiStatus(statusRes);

      const convList = convListRes.conversations || [];
      setConversations(convList);

      // Check URL query param for productId (e.g. redirected from Product Details "Ask AI")
      const queryProdId = searchParams.get('productId');
      if (queryProdId && prodList.some(p => p.id === queryProdId)) {
        setContextMode('product');
        setSelectedProductId(queryProdId);
        // Create or find a conversation for this product
        await handleStartNewConversation('product', queryProdId, prodList);
      } else if (convList.length > 0) {
        // Load latest conversation
        await loadConversationDetail(convList[0].id);
      } else {
        // Create first Global conversation
        await handleStartNewConversation('global', '', prodList);
      }
    } catch (err) {
      console.error('Error loading AI Assistant initial state:', err);
    } finally {
      setLoadingInitial(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchInitial();
  }, [fetchInitial]);

  // 2. Load Conversation Details & Messages
  const loadConversationDetail = async (convId) => {
    try {
      setLoadingConversation(true);
      const res = await aiApi.getConversation(convId);
      setCurrentConversationId(convId);
      setCurrentConversation(res.conversation);
      setContextMode(res.conversation.contextType || 'global');
      if (res.conversation.productId) {
        setSelectedProductId(res.conversation.productId);
      }
      setMessages(res.messages || []);
    } catch (err) {
      console.error('Error loading conversation detail:', err);
    } finally {
      setLoadingConversation(false);
    }
  };

  // 3. Start New Conversation Thread
  const handleStartNewConversation = async (mode = contextMode, prodId = selectedProductId, currentProdList = products) => {
    try {
      setLoadingConversation(true);
      let title = mode === 'product' ? 'Product Assistant' : 'Global OWNIT Assistant';
      if (mode === 'product' && prodId) {
        const prod = currentProdList.find(p => p.id === prodId);
        if (prod) title = `${prod.brand} ${prod.name} Chat`;
      }

      const newConv = await aiApi.createConversation({
        contextType: mode,
        productId: mode === 'product' ? prodId : null,
        title
      });

      setConversations(prev => [newConv, ...prev.filter(c => c.id !== newConv.id)]);
      setCurrentConversationId(newConv.id);
      setCurrentConversation(newConv);
      setContextMode(mode);
      if (mode === 'product') {
        setSelectedProductId(prodId);
      }
      setMessages([]);
    } catch (err) {
      console.error('Error creating new conversation:', err);
    } finally {
      setLoadingConversation(false);
    }
  };

  // 4. Delete Conversation
  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    try {
      await aiApi.deleteConversation(convId);
      const updated = conversations.filter(c => c.id !== convId);
      setConversations(updated);
      if (currentConversationId === convId) {
        if (updated.length > 0) {
          loadConversationDetail(updated[0].id);
        } else {
          handleStartNewConversation('global', '');
        }
      }
    } catch (err) {
      alert(`Could not delete conversation: ${err.message}`);
    }
  };

  // 5. Send Message
  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading || !currentConversationId) return;

    const tempUserMsg = {
      id: `temp-user-${Date.now()}`,
      conversationId: currentConversationId,
      role: 'user',
      content: text,
      sources: [],
      sourceReferences: [],
      actions: [],
      createdAt: new Date().toISOString()
    };

    setMessages(prev => [...prev, tempUserMsg]);
    setInputMessage('');
    setLoading(true);

    try {
      const resMsg = await aiApi.sendConversationMessage(currentConversationId, {
        message: text,
        contextType: contextMode,
        productId: contextMode === 'product' ? selectedProductId : null
      });

      setMessages(prev => {
        const withoutTemp = prev.filter(m => m.id !== tempUserMsg.id);
        return [...withoutTemp, tempUserMsg, resMsg];
      });

      // Update last message in sidebar list
      setConversations(prev => prev.map(c => {
        if (c.id === currentConversationId) {
          return { ...c, lastMessage: resMsg.content.slice(0, 80), updatedAt: new Date().toISOString() };
        }
        return c;
      }));
    } catch (err) {
      console.error('Error sending AI message:', err);
      const errMsg = {
        id: `err-${Date.now()}`,
        conversationId: currentConversationId,
        role: 'assistant',
        content: `⚠️ ${err.message || 'Could not reach local AI service.'}`,
        sources: ['Connection Error'],
        sourceReferences: [],
        actions: [],
        createdAt: new Date().toISOString()
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  // 6. Action Button Handler
  const handleExecuteAction = (action) => {
    if (action.route) {
      navigate(action.route);
    } else if (action.params?.productId) {
      navigate(`/products/${action.params.productId}`);
    }
  };

  // Suggested Prompts based on Mode and Language
  const globalSuggestedPrompts = language === 'hi' ? [
    "मेरे पास कितने उत्पाद पंजीकृत हैं?",
    "कौन सी वारंटी जल्द समाप्त हो रही हैं?",
    "किस उपकरण का लाइफ स्कोर सबसे कम है?",
    "क्या मैं अभी किसी वस्तु को वापस कर सकता हूँ?"
  ] : language === 'te' ? [
    "నా వద్ద మొత్తం ఎన్ని ఉత్పత్తులు ఉన్నాయి?",
    "ఏ వారంటీలు త్వరలో గడువు ముగుస్తాయి?",
    "ఏ పరికరానికి లైఫ్ స్కోర్ తక్కువగా ఉంది?",
    "నేను ఇంకా ఏ వస్తువులను రిటర్న్ చేయగలను?"
  ] : [
    "How many products do I have registered?",
    "Which warranties are expiring soon?",
    "Which device has the lowest Life Score?",
    "What items are eligible for return?"
  ];

  const productSuggestedPrompts = language === 'hi' ? [
    "मेरी वारंटी के तहत क्या कवर किया गया है?",
    "मुझे इस वस्तु को कैसे साफ और बनाए रखना चाहिए?",
    "वारंटी के बहिष्करण (exclusions) क्या हैं?",
    "ग्राहक सहायता के लिए वारंटी दावा संदेश का मसौदा तैयार करें"
  ] : language === 'te' ? [
    "నా వారంటీ కింద ఏమి కవర్ చేయబడింది?",
    "ఈ వస్తువును ఎలా శుభ్రం చేయాలి మరియు నిర్వహించాలి?",
    "వారంటీ మినహాయింపులు ఏమిటి?",
    "కస్టమర్ సపోర్ట్ కోసం క్లెయిమ్ సందేశాన్ని డ్రాఫ్ట్ చేయండి"
  ] : [
    "What is covered under my warranty?",
    "How should I clean and maintain this item?",
    "What are the explicit warranty exclusions?",
    "Draft a warranty claim message for support"
  ];

  const currentPrompts = contextMode === 'product' ? productSuggestedPrompts : globalSuggestedPrompts;
  const currentProduct = products.find(p => p.id === selectedProductId);

  return (
    <PageContainer
      title={contextMode === 'product' && currentProduct ? `AI Assistant · ${formatProductName(currentProduct.brand, currentProduct.name)}` : 'Global OWNIT AI Assistant'}
      subtitle={contextMode === 'product' ? 'Context-anchored assistant for warranties, manuals, maintenance, and support.' : 'Unified intelligence across your entire product catalog, warranties, and receipts.'}
      actions={
        <div className="ai-status-tag">
          <Cpu size={16} />
          <span>
            {aiStatus?.isAvailable
              ? `Local Engine: ${aiStatus.configuredModel} (Ollama)`
              : 'Local Engine: Offline Fallback'}
          </span>
        </div>
      }
    >
      {loadingInitial ? (
        <LoadingState message="Connecting to OWNIT AI..." description="Loading conversations and catalog context..." />
      ) : (
        <div className="ai-workspace-layout">
          {/* Left Panel: Conversation Threads & Context Scope */}
          <div className="ai-threads-sidebar">
            <div className="new-chat-row">
              <Button
                variant="primary"
                icon={Plus}
                onClick={() => handleStartNewConversation(contextMode, selectedProductId)}
                className="new-chat-btn"
              >
                {t('ai.newChat', {}, 'New Conversation')}
              </Button>
            </div>

            {/* Context Switcher Card */}
            <Card className="context-switcher-card" padding="sm">
              <span className="context-section-label">{t('ai.contextMode', {}, 'Context Mode')}</span>
              <div className="context-mode-buttons">
                <button
                  className={`context-mode-btn ${contextMode === 'global' ? 'active' : ''}`}
                  onClick={() => {
                    setContextMode('global');
                    handleStartNewConversation('global', '');
                  }}
                >
                  <Globe size={15} />
                  <span>{t('ai.globalMode', {}, 'Global (All Items)')}</span>
                </button>
                <button
                  className={`context-mode-btn ${contextMode === 'product' ? 'active' : ''}`}
                  onClick={() => {
                    setContextMode('product');
                    const defaultProdId = selectedProductId || (products[0]?.id || '');
                    setSelectedProductId(defaultProdId);
                    handleStartNewConversation('product', defaultProdId);
                  }}
                  disabled={products.length === 0}
                >
                  <Package size={15} />
                  <span>{t('ai.productMode', {}, 'Specific Product')}</span>
                </button>
              </div>

              {contextMode === 'product' && products.length > 0 && (
                <div className="product-picker-wrap">
                  <label className="picker-label">{t('ai.selectProduct', {}, 'Target Product')}:</label>
                  <select
                    className="ai-product-dropdown"
                    value={selectedProductId}
                    onChange={(e) => {
                      const newProdId = e.target.value;
                      setSelectedProductId(newProdId);
                      handleStartNewConversation('product', newProdId);
                    }}
                  >
                    {products.map(p => (
                      <option key={p.id} value={p.id}>
                        {formatProductName(p.brand, p.name)} {p.model ? `(${p.model})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </Card>

            {/* Conversation History List */}
            <div className="threads-list-card">
              <div className="threads-list-header">
                <span className="threads-header-title">{t('ai.conversations', {}, 'Recent Conversations')}</span>
                <Badge variant="neutral" size="sm">{conversations.length}</Badge>
              </div>

              <div className="threads-scroll-area">
                {conversations.length === 0 ? (
                  <div className="no-threads-msg">
                    <MessageSquare size={20} />
                    <span>No conversations yet</span>
                  </div>
                ) : (
                  conversations.map(conv => {
                    const isSelected = conv.id === currentConversationId;
                    return (
                      <div
                        key={conv.id}
                        className={`thread-item ${isSelected ? 'active' : ''}`}
                        onClick={() => loadConversationDetail(conv.id)}
                      >
                        <div className="thread-item-icon">
                          {conv.contextType === 'product' ? <Package size={14} /> : <Globe size={14} />}
                        </div>
                        <div className="thread-item-info">
                          <div className="thread-item-title">{conv.title}</div>
                          <div className="thread-item-preview">
                            {conv.lastMessage || 'No messages yet'}
                          </div>
                        </div>
                        <button
                          className="thread-delete-btn"
                          onClick={(e) => handleDeleteConversation(conv.id, e)}
                          title="Delete thread"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Right Panel: Active Chat Thread */}
          <div className="ai-main-chat-panel">
            <Card className="ai-chat-container-card" padding="none">
              {/* Context Banner Bar */}
              <div className="ai-chat-context-banner">
                <div className="banner-left">
                  {contextMode === 'product' && currentProduct ? (
                    <>
                      <Package size={18} className="banner-icon-product" />
                      <div>
                        <div className="banner-title">{formatProductName(currentProduct.brand, currentProduct.name)}</div>
                        <div className="banner-sub">Model: {currentProduct.model || 'N/A'} · Category: {currentProduct.category} · Life Score: {currentProduct.lifeScore || 80}/100</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <Globe size={18} className="banner-icon-global" />
                      <div>
                        <div className="banner-title">Global Portfolio Intelligence</div>
                        <div className="banner-sub">Cross-product reasoning across {products.length} registered asset(s) and warranties</div>
                      </div>
                    </>
                  )}
                </div>

                <div className="banner-right">
                  <Badge variant={aiStatus?.isAvailable ? 'active' : 'warning'} size="sm" dot>
                    {aiStatus?.isAvailable ? `Ollama (${aiStatus.configuredModel})` : 'Offline Fallback'}
                  </Badge>
                </div>
              </div>

              {/* Messages Area */}
              <div className="ai-messages-scroll">
                {loadingConversation ? (
                  <div className="chat-loading-box">
                    <RefreshCw size={24} className="spinning" />
                    <span>Loading conversation...</span>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="chat-welcome-box">
                    <div className="welcome-avatar">
                      <Bot size={28} />
                    </div>
                    <h3 className="welcome-heading">
                      {contextMode === 'product' && currentProduct
                        ? `Welcome to ${currentProduct.brand} ${currentProduct.name} Assistant`
                        : 'Welcome to OWNIT Global Assistant'}
                    </h3>
                    <p className="welcome-sub">
                      {contextMode === 'product' && currentProduct
                        ? `I have instant access to your registered warranties, invoices, maintenance logs, and repair history for this ${currentProduct.category}. Ask me anything about warranty claims, care tips, or coverage!`
                        : `I can help you monitor warranties, review return deadlines, compare life scores, or manage maintenance across all ${products.length} of your registered items.`}
                    </p>
                  </div>
                ) : (
                  messages.map(msg => {
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
                              {isUser ? 'You' : (contextMode === 'product' && currentProduct ? `${currentProduct.brand} Assistant` : 'OWNIT Assistant')}
                            </span>
                            <span className="chat-time">
                              {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>

                          <div className="chat-text" style={{ whiteSpace: 'pre-line' }}>
                            {msg.content}
                          </div>

                          {/* Action Buttons */}
                          {!isUser && msg.actions && msg.actions.length > 0 && (
                            <div className="chat-actions-row">
                              {msg.actions.map((act, aIdx) => (
                                <button
                                  key={aIdx}
                                  className="chat-action-btn"
                                  onClick={() => handleExecuteAction(act)}
                                >
                                  <span>{act.label}</span>
                                  <ArrowRight size={12} />
                                </button>
                              ))}
                            </div>
                          )}

                          {/* Sourced References Pills */}
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
              <div className="ai-chat-quick-prompts">
                <span className="quick-prompts-label">
                  <Sparkles size={13} /> {t('ai.sourcesUsed', {}, 'Suggested')}:
                </span>
                <div className="quick-prompts-row">
                  {currentPrompts.map((prompt, idx) => (
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

              {/* Input Bar */}
              <div className="ai-chat-input-bar">
                <input
                  type="text"
                  placeholder={
                    contextMode === 'product' && currentProduct
                      ? `Ask about ${currentProduct.name} warranty, maintenance, or claim steps...`
                      : 'Ask anything across your products, warranties, receipts, or return deadlines...'
                  }
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  disabled={loading}
                  className="ai-chat-input"
                />
                <Button
                  variant="primary"
                  icon={Send}
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || loading}
                >
                  {t('ai.send', {}, 'Send')}
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
