import React, { useState } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  User,
  ShieldCheck,
  FileText,
  HelpCircle,
  Cpu
} from 'lucide-react';
import PageContainer from '../../components/layout/PageContainer';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import { mockProducts, mockChatPresets } from '../../data/mockData';
import './AIAssistant.css';

export default function AIAssistant() {
  const [selectedProduct, setSelectedProduct] = useState(mockProducts[0].id);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: `Hello! I am your OWNIT Local AI Assistant running private inference with Ollama. Select any product from your catalog and ask about warranty coverage, claim drafting, maintenance intervals, or troubleshooting!`,
      timestamp: 'Just now'
    }
  ]);

  const handleSendMessage = (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: text,
      timestamp: 'Just now'
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');

    // Simulate local AI response after a brief delay for frontend presentation
    setTimeout(() => {
      const selectedProdObj = mockProducts.find((p) => p.id === selectedProduct) || mockProducts[0];
      const aiReply = {
        id: Date.now() + 1,
        sender: 'ai',
        text: `Based on your ${selectedProdObj.name} records and warranty documents:

• **Warranty Status**: ${selectedProdObj.warrantyStatus.toUpperCase()} (Expires ${selectedProdObj.warrantyExpiry})
• **Provider**: ${selectedProdObj.warrantyDetails.provider}
• **Inclusions**: ${selectedProdObj.warrantyDetails.inclusions.join(', ')}

💡 *Tip for student demonstration: In the next backend module, this will be connected to your local Ollama LLM to parse real manuals and draft actual claim letters.*`,
        timestamp: 'Just now'
      };
      setMessages((prev) => [...prev, aiReply]);
    }, 600);
  };

  return (
    <PageContainer
      title="Product AI Assistant"
      subtitle="Interact with your documents and warranty terms privately using local Ollama LLM inference."
      actions={
        <div className="ai-status-tag">
          <Cpu size={16} />
          <span>Local Engine: LLaMA 3.2 (Ollama)</span>
        </div>
      }
    >
      <div className="ai-chat-layout">
        {/* Left Side: Product Selector & Preset Prompts */}
        <div className="ai-sidebar-col">
          <Card title="Context Product">
            <div className="product-selector-group">
              <label className="selector-label">Active Device for Query:</label>
              <select
                className="ai-product-select"
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
              >
                {mockProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.brand})
                  </option>
                ))}
              </select>
            </div>
          </Card>

          <Card title="Quick Suggested Prompts" subtitle="Click any prompt to ask the AI:">
            <div className="preset-prompts-list">
              {mockChatPresets.map((preset, idx) => (
                <button
                  key={idx}
                  className="preset-prompt-btn"
                  onClick={() => handleSendMessage(preset)}
                >
                  <Sparkles size={14} className="preset-icon" />
                  <span>{preset}</span>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Side: Chat Window */}
        <div className="ai-chat-col">
          <Card className="ai-chat-card" padding="none">
            {/* Chat Messages */}
            <div className="chat-messages-container">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-bubble-row ${msg.sender === 'user' ? 'chat-row-user' : 'chat-row-ai'}`}
                >
                  <div className={`chat-avatar ${msg.sender === 'user' ? 'avatar-user' : 'avatar-ai'}`}>
                    {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  <div className="chat-bubble-content">
                    <div className="chat-bubble-header">
                      <span className="chat-sender-name">
                        {msg.sender === 'user' ? 'You' : 'OWNIT Local AI'}
                      </span>
                      <span className="chat-time">{msg.timestamp}</span>
                    </div>
                    <div className="chat-text" style={{ whiteSpace: 'pre-line' }}>
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Input Bar */}
            <div className="chat-input-bar">
              <input
                type="text"
                placeholder="Ask about warranty terms, maintenance, or claim drafting..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSendMessage();
                }}
                className="chat-input-field"
              />
              <Button
                variant="primary"
                icon={Send}
                onClick={() => handleSendMessage()}
                disabled={!inputMessage.trim()}
              >
                Send
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}
