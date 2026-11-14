import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";

export default function Hero({ onSelectCategory }) {
  return (
    <section className="hero-section">
      <div className="hero-grid">
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="eyebrow-line" />
            <span>ISSUE 04 • CURATED FASHION INTELLIGENCE</span>
          </div>
          <h1 className="hero-headline">
            Quiet Architecture for the <em>Modern Wardrobe.</em>
          </h1>
          <p className="hero-description">
            Discover architectural silhouettes, breathable natural fibers, and timeless essentials curated across
            India’s premier luxury and contemporary fashion houses in one editorial space.
          </p>
          <div className="hero-cta-group">
            <a href="#discovery-grid" className="btn-primary">
              <span>Explore the Archive</span>
              <ArrowRight size={16} />
            </a>
            <Link to="/stylist" className="btn-secondary">
              <Sparkles size={16} />
              <span>Consult AI Stylist</span>
            </Link>
          </div>
          <div className="hero-metrics">
            <div className="metric-item">
              <span className="metric-num">06+</span>
              <span className="metric-label">Premier Concept Stores</span>
            </div>
            <div className="metric-divider" />
            <div className="metric-item">
              <span className="metric-num">100%</span>
              <span className="metric-label">Editorial Selection</span>
            </div>
            <div className="metric-divider" />
            <div className="metric-item">
              <span className="metric-num">INR</span>
              <span className="metric-label">Direct Store Pricing</span>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-image-frame">
            <img
              src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=1200&q=85"
              alt="HANGER Editorial Lookbook"
              className="hero-main-img"
            />
            <div className="hero-floating-card" onClick={() => onSelectCategory && onSelectCategory("Outerwear")}>
              <span className="floating-tag">FEATURED SILHOUETTE</span>
              <p className="floating-title">Belgian Flax & Chanderi Silk</p>
              <span className="floating-link">View Outerwear &rarr;</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
