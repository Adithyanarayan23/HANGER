import React, { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Sparkles } from "lucide-react";
import ProductGrid from "../components/ProductGrid";
import { PRODUCTS, CURATED_COLLECTIONS } from "../data/products";
import "../styles/home.css";
import "../styles/products.css";

export default function Recommendations() {
  const [selectedCollection, setSelectedCollection] = useState("All");
  const [budgetTier, setBudgetTier] = useState("UNDER_6000");

  const trendingProducts = PRODUCTS.filter((p) => p.trending);

  const collectionProducts =
    selectedCollection === "All"
      ? PRODUCTS.slice(0, 8)
      : PRODUCTS.filter((p) => p.collection === selectedCollection);

  const budgetProducts = PRODUCTS.filter((p) => {
    if (budgetTier === "UNDER_6000") return p.price <= 6000;
    if (budgetTier === "6000_10000") return p.price > 6000 && p.price <= 10000;
    return p.price > 10000;
  });

  const relatedPairings = PRODUCTS.filter((p) =>
    ["hng-001", "hng-014", "hng-005", "hng-006"].includes(p.id)
  );

  return (
    <div className="recommendations-page">
      {/* Page Hero */}
      <section className="rec-hero-section">
        <div className="section-container">
          <span className="section-kicker">CURATED ARCHIVE & SEASONAL EDITS</span>
          <h1 className="page-hero-title">
            Editorial <em>Recommendations</em>
          </h1>
          <p className="rec-hero-subtitle">
            Thoughtfully assembled capsules spanning tactile linen resortwear, monochrome architectural tailoring, and
            price-conscious wardrobe foundations.
          </p>
        </div>
      </section>

      {/* 1. Curated Collections */}
      <section className="rec-collections-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">CAPSULE STORIES</span>
              <h2 className="section-title">Curated Collections</h2>
            </div>
            {selectedCollection !== "All" && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setSelectedCollection("All")}
              >
                <span>Show All Capsules</span>
              </button>
            )}
          </div>

          <div className="curated-cards-grid">
            {CURATED_COLLECTIONS.map((col) => (
              <div
                key={col.id}
                className={`curated-story-card ${
                  selectedCollection === col.filterKey ? "active-story" : ""
                }`}
                onClick={() => setSelectedCollection(col.filterKey)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) =>
                  e.key === "Enter" && setSelectedCollection(col.filterKey)
                }
              >
                <div className="story-img-wrap">
                  <img src={col.image} alt={col.title} />
                  <span className="story-tag">{col.tag}</span>
                </div>
                <div className="story-body">
                  <h3>{col.title}</h3>
                  <p>{col.subtitle}</p>
                  <span className="story-action">
                    Filter Capsule <ArrowUpRight size={14} />
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="capsule-filtered-block">
            <div className="capsule-sub-bar">
              <span>
                Currently viewing:{" "}
                <strong>
                  {selectedCollection === "All"
                    ? "All Seasonal Capsules"
                    : selectedCollection}
                </strong>
              </span>
            </div>
            <ProductGrid products={collectionProducts} />
          </div>
        </div>
      </section>

      {/* 2. Trending Products */}
      <section className="rec-trending-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">MOST INSPECTED THIS WEEK</span>
              <h2 className="section-title">Trending Archive Pieces</h2>
            </div>
            <Link to="/search" className="section-link-arrow">
              <span>Full Catalog</span>
              <ArrowUpRight size={16} />
            </Link>
          </div>
          <ProductGrid products={trendingProducts} />
        </div>
      </section>

      {/* 3. Editorial Fashion Essay Section */}
      <section className="rec-editorial-feature">
        <div className="section-container">
          <div className="editorial-split-box">
            <div className="editorial-split-image">
              <img
                src="https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1000&q=85"
                alt="Editorial Essay: The Weight of Natural Fibers"
              />
            </div>
            <div className="editorial-split-text">
              <span className="section-kicker">ATELIER JOURNAL • ESSAY 07</span>
              <h2>The Quiet Permanence of Unlined Tailoring</h2>
              <p>
                Modern Indian wardrobes demand garments that move effortlessly between climate-controlled studios and
                warm coastal evenings. By replacing synthetic interlinings with high-twist European flax linen, spun
                mulberry silk, and handwoven Chanderi, structure is achieved through cut rather than stiffness.
              </p>
              <p>
                Our curation prioritizes natural fibers that soften with every wear while maintaining crisp architectural
                lines at the collar and cuff.
              </p>
              <Link to="/stylist" className="btn-primary">
                <Sparkles size={16} />
                <span>Build Your Capsule with AI Stylist</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Budget-Based Collections */}
      <section className="rec-budget-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">PRICE-CONSCIOUS CURATION</span>
              <h2 className="section-title">Budget-Based Edits (INR)</h2>
            </div>
            <div className="budget-tabs">
              <button
                type="button"
                className={`category-pill-btn ${
                  budgetTier === "UNDER_6000" ? "active" : ""
                }`}
                onClick={() => setBudgetTier("UNDER_6000")}
              >
                Under ₹6,000
              </button>
              <button
                type="button"
                className={`category-pill-btn ${
                  budgetTier === "6000_10000" ? "active" : ""
                }`}
                onClick={() => setBudgetTier("6000_10000")}
              >
                ₹6,000 – ₹10,000
              </button>
              <button
                type="button"
                className={`category-pill-btn ${
                  budgetTier === "ABOVE_10000" ? "active" : ""
                }`}
                onClick={() => setBudgetTier("ABOVE_10000")}
              >
                Investment Pieces (₹10,000+)
              </button>
            </div>
          </div>

          <ProductGrid products={budgetProducts} />
        </div>
      </section>

      {/* 5. Complete Look / Related Pairings */}
      <section className="rec-related-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">STYLIST FORMULA 01</span>
              <h2 className="section-title">Related Ensemble: The Sand & Calfskin Edit</h2>
            </div>
          </div>
          <ProductGrid products={relatedPairings} />
        </div>
      </section>
    </div>
  );
}
