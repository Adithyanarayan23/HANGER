import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Sparkles,
  Send,
  Trash2,
  Plus,
  MessageSquare,
  ArrowUpRight,
  Info
} from "lucide-react";
import { PRODUCTS, formatINR } from "../data/products";
import {
  SUGGESTED_PROMPTS,
  INITIAL_CONVERSATIONS,
  generateStylistReply
} from "../services/chatService";
import "../styles/chat.css";

export default function ChatAssistant() {
  const [conversations, setConversations] = useState(INITIAL_CONVERSATIONS);
  const [activeConvId, setActiveConvId] = useState(INITIAL_CONVERSATIONS[0].id);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const activeConversation =
    conversations.find((c) => c.id === activeConvId) || conversations[0];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages, isTyping]);

  const handleSendMessage = (promptOverride) => {
    const textToSend = (promptOverride ?? inputText).trim();
    if (!textToSend || isTyping) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: "user",
      timestamp: "Just now",
      text: textToSend
    };

    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== activeConvId) return conv;
        const updatedTitle =
          conv.messages.length <= 1
            ? textToSend.slice(0, 32) + (textToSend.length > 32 ? "..." : "")
            : conv.title;
        return {
          ...conv,
          title: updatedTitle,
          updatedAt: "Just now",
          messages: [...conv.messages, userMsg]
        };
      })
    );

    if (!promptOverride) setInputText("");
    setIsTyping(true);

    setTimeout(() => {
      const reply = generateStylistReply(textToSend);
      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: "assistant",
        timestamp: "Just now",
        text: reply.text,
        stylistNote: reply.stylistNote,
        recommendations: reply.products.map((p) => p.id)
      };

      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConvId
            ? { ...conv, messages: [...conv.messages, botMsg] }
            : conv
        )
      );
      setIsTyping(false);
    }, 550);
  };

  const handleNewConversation = () => {
    const newId = `conv-${Date.now()}`;
    const freshConv = {
      id: newId,
      title: "New Styling Session",
      updatedAt: "Just now",
      messages: [
        {
          id: `welcome-${Date.now()}`,
          sender: "assistant",
          timestamp: "Just now",
          text: "New styling session started. Tell me about an occasion, preferred fabric, color palette, or budget in INR and I will assemble a cohesive edit.",
          recommendations: ["hng-001", "hng-003", "hng-005"]
        }
      ]
    };
    setConversations((prev) => [freshConv, ...prev]);
    setActiveConvId(newId);
  };

  const handleClearCurrentConversation = () => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConvId
          ? {
              ...conv,
              title: "Cleared Session",
              messages: [
                {
                  id: `reset-${Date.now()}`,
                  sender: "assistant",
                  timestamp: "Just now",
                  text: "Conversation cleared. Choose a suggested prompt below or describe the look you would like to curate.",
                  recommendations: []
                }
              ]
            }
          : conv
      )
    );
  };

  const resolveProducts = (idList = []) => {
    return idList.map((pid) => PRODUCTS.find((p) => p.id === pid)).filter(Boolean);
  };

  return (
    <div className="chat-assistant-page">
      <div className="chat-layout-container">
        {/* Left Sidebar: Chat History & Branding */}
        <aside className="chat-sidebar">
          <div className="chat-sidebar-brand">
            <div className="sidebar-brand-badge">
              <Sparkles size={15} />
              <span>HANGER AI ATELIER</span>
            </div>
            <p className="sidebar-brand-caption">
              Interactive Editorial Styling & Outfit Curation
            </p>
          </div>

          <button
            type="button"
            className="new-session-btn"
            onClick={handleNewConversation}
          >
            <Plus size={16} />
            <span>New Styling Session</span>
          </button>

          <div className="chat-history-section">
            <span className="history-label">RECENT SESSIONS</span>
            <ul className="chat-history-list">
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <button
                    type="button"
                    className={`history-item-btn ${
                      conv.id === activeConvId ? "active" : ""
                    }`}
                    onClick={() => setActiveConvId(conv.id)}
                  >
                    <MessageSquare size={14} />
                    <div className="history-item-text">
                      <span className="history-title">{conv.title}</span>
                      <span className="history-time">{conv.updatedAt}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="chat-sidebar-footer">
            <div className="demo-disclaimer-box">
              <Info size={14} />
              <p>
                <strong>Frontend Demo Mode:</strong> Responses are powered by local
                curated styling logic and mock catalog data.
              </p>
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <section className="chat-main-panel">
          {/* Chat Topbar */}
          <header className="chat-panel-header">
            <div>
              <span className="chat-header-kicker">PERSONAL WARDROBE CURATOR</span>
              <h1 className="chat-header-title">{activeConversation.title}</h1>
            </div>

            <button
              type="button"
              className="clear-chat-btn"
              onClick={handleClearCurrentConversation}
              title="Clear conversation"
            >
              <Trash2 size={15} />
              <span>Clear Conversation</span>
            </button>
          </header>

          {/* Message Stream */}
          <div className="chat-messages-stream">
            {activeConversation.messages.map((msg) => {
              const recommendedProducts = resolveProducts(msg.recommendations);

              return (
                <div
                  key={msg.id}
                  className={`chat-bubble-row ${
                    msg.sender === "user" ? "row-user" : "row-assistant"
                  }`}
                >
                  <div className="chat-bubble-avatar">
                    {msg.sender === "user" ? "YOU" : "H"}
                  </div>

                  <div className="chat-bubble-content">
                    <div className="chat-bubble-meta">
                      <span className="bubble-author">
                        {msg.sender === "user" ? "Client" : "HANGER Stylist"}
                      </span>
                      <span className="bubble-time">{msg.timestamp}</span>
                    </div>

                    <div className="chat-bubble-card">
                      <p className="bubble-text">{msg.text}</p>
                      {msg.stylistNote && (
                        <div className="stylist-tip-box">
                          <strong>Stylist Note:</strong> {msg.stylistNote}
                        </div>
                      )}
                    </div>

                    {/* Product Recommendation Cards inside Chat */}
                    {recommendedProducts.length > 0 && (
                      <div className="chat-recommendations-block">
                        <span className="chat-rec-label">
                          CURATED PIECES FROM ARCHIVE ({recommendedProducts.length})
                        </span>
                        <div className="chat-rec-grid">
                          {recommendedProducts.map((item) => (
                            <div key={item.id} className="chat-rec-card">
                              <Link
                                to={`/product/${item.id}`}
                                className="chat-rec-img-wrap"
                              >
                                <img src={item.image} alt={item.name} />
                              </Link>
                              <div className="chat-rec-info">
                                <span className="chat-rec-brand">{item.brand}</span>
                                <Link
                                  to={`/product/${item.id}`}
                                  className="chat-rec-name"
                                >
                                  {item.name}
                                </Link>
                                <div className="chat-rec-bottom">
                                  <span className="chat-rec-price">
                                    {formatINR(item.price)}
                                  </span>
                                  <Link
                                    to={`/product/${item.id}`}
                                    className="chat-rec-link"
                                  >
                                    Inspect <ArrowUpRight size={12} />
                                  </Link>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="chat-bubble-row row-assistant">
                <div className="chat-bubble-avatar">H</div>
                <div className="chat-bubble-content">
                  <div className="chat-bubble-card typing-indicator-card">
                    <span>Curating archival lookbook pieces...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Prompts */}
          <div className="chat-prompts-bar">
            <span className="prompts-bar-label">Suggested Styling Prompts:</span>
            <div className="prompts-scroll-row">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="prompt-chip-btn"
                  onClick={() => handleSendMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Input Composer */}
          <form
            className="chat-composer-form"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            <input
              type="text"
              className="chat-composer-input"
              placeholder="Ask for an outfit formula, fabric pairing, or occasion edit (e.g., 'Coastal linen capsule')..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!inputText.trim() || isTyping}
            >
              <span>Send</span>
              <Send size={15} />
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
