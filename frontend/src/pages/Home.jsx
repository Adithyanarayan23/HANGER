import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowUpRight, Sparkles, SlidersHorizontal, RotateCcw } from "lucide-react";
import Hero from "../components/Hero";
import SearchBar from "../components/SearchBar";
import ProductGrid from "../components/ProductGrid";
import { PRODUCTS, CATEGORIES } from "../data/products";
import { useProductFilters } from "../hooks/useProductFilters";
import "../styles/home.css";
import "../styles/products.css";

export default function Home() {
  const navigate = useNavigate();
  const {
    searchQuery,
    setSearchQuery,
    selectedCategory,
    setSelectedCategory,
    selectedBrand,
    setSelectedBrand,
    selectedColor,
    setSelectedColor,
    priceRange,
    setPriceRange,
    sortBy,
    setSortBy,
    brands,
    colors,
    categories,
    filteredProducts,
    resetFilters,
    activeFilterCount
  } = useProductFilters(PRODUCTS);

  const handleCategoryTileClick = (categoryId) => {
    setSelectedCategory(categoryId);
    const gridEl = document.getElementById("discovery-grid");
    if (gridEl) {
      gridEl.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleSearchSubmit = (queryText) => {
    if (queryText && queryText.trim().length > 0) {
      navigate(`/search?q=${encodeURIComponent(queryText.trim())}`);
    } else {
      const gridEl = document.getElementById("discovery-grid");
      if (gridEl) gridEl.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setSearchQuery(suggestion);
    const gridEl = document.getElementById("discovery-grid");
    if (gridEl) gridEl.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="home-page">
      {/* 1. Hero Section */}
      <Hero onSelectCategory={handleCategoryTileClick} />

      {/* 2. Natural-Language Search & Suggestions Section */}
      <section className="home-search-section">
        <div className="section-container">
          <div className="search-editorial-header">
            <span className="section-kicker">NATURAL LANGUAGE DISCOVERY</span>
            <h2 className="section-title">Search by Silhouette, Mood, or Textile</h2>
          </div>
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSubmit={handleSearchSubmit}
            onSuggestionClick={handleSuggestionClick}
            showSuggestions={true}
          />
        </div>
      </section>

      {/* 3. Fashion Category Tiles */}
      <section id="categories-section" className="home-categories-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">CURATED DEPARTMENTS</span>
              <h2 className="section-title">Explore by Silhouette</h2>
            </div>
            <Link to="/search" className="section-link-arrow">
              <span>View Full Index</span>
              <ArrowUpRight size={16} />
            </Link>
          </div>

          <div className="category-tiles-grid">
            {CATEGORIES.map((cat) => (
              <div
                key={cat.id}
                className={`category-tile ${selectedCategory === cat.id ? "selected-tile" : ""}`}
                onClick={() => handleCategoryTileClick(cat.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && handleCategoryTileClick(cat.id)}
              >
                <img src={cat.image} alt={cat.name} className="category-tile-img" loading="lazy" />
                <div className="category-tile-overlay">
                  <span className="category-tile-count">{cat.count}</span>
                  <h3 className="category-tile-title">{cat.name}</h3>
                  <p className="category-tile-sub">{cat.subtitle}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Product Discovery Grid with Working Filters & Sorting */}
      <section id="discovery-grid" className="home-discovery-section">
        <div className="section-container">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">THE SEASONAL EDIT</span>
              <h2 className="section-title">Curated Product Archive</h2>
            </div>
            <div className="results-counter">
              Showing <strong>{filteredProducts.length}</strong> of {PRODUCTS.length} pieces
            </div>
          </div>

          {/* Horizontal Filter & Sort Bar */}
          <div className="discovery-toolbar">
            <div className="toolbar-categories">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`category-pill-btn ${selectedCategory === cat ? "active" : ""}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="toolbar-selects">
              <div className="select-item">
                <SlidersHorizontal size={14} className="select-icon" />
                <select
                  value={selectedBrand}
                  onChange={(e) => setSelectedBrand(e.target.value)}
                  aria-label="Filter by brand"
                >
                  {brands.map((b) => (
                    <option key={b} value={b}>
                      {b === "All" ? "Brand: All" : b}
                    </option>
                  ))}
                </select>
              </div>

              <div className="select-item">
                <select
                  value={selectedColor}
                  onChange={(e) => setSelectedColor(e.target.value)}
                  aria-label="Filter by color"
                >
                  {colors.map((c) => (
                    <option key={c} value={c}>
                      {c === "All" ? "Palette: All" : c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="select-item">
                <select
                  value={priceRange}
                  onChange={(e) => setPriceRange(e.target.value)}
                  aria-label="Filter by price range"
                >
                  <option value="ALL">Price: All Tiers</option>
                  <option value="UNDER_5000">Under ₹5,000</option>
                  <option value="5000_10000">₹5,000 – ₹10,000</option>
                  <option value="ABOVE_10000">Above ₹10,000</option>
                </select>
              </div>

              <div className="select-item">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  aria-label="Sort products"
                >
                  <option value="featured">Sort: Editorial Picks</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="brand-asc">Brand: A – Z</option>
                </select>
              </div>

              {activeFilterCount > 0 && (
                <button type="button" className="toolbar-reset-btn" onClick={resetFilters}>
                  <RotateCcw size={14} />
                  <span>Reset ({activeFilterCount})</span>
                </button>
              )}
            </div>
          </div>

          <ProductGrid products={filteredProducts} onResetFilters={resetFilters} />
        </div>
      </section>

      {/* 5. AI Stylist Promotional Banner */}
      <section className="stylist-promo-section">
        <div className="section-container">
          <div className="stylist-promo-banner">
            <div className="stylist-promo-text">
              <div className="promo-badge">
                <Sparkles size={14} />
                <span>HANGER PERSONAL ATELIER</span>
              </div>
              <h2 className="promo-title">
                Not sure how to pair a piece? Speak with the <em>AI Fashion Stylist.</em>
              </h2>
              <p className="promo-description">
                Describe an upcoming coastal getaway, an evening gallery reception, or your preferred color palette.
                Receive instant, cohesive outfit formulas drawn from our curated multi-store archive.
              </p>
              <div className="promo-actions">
                <Link to="/stylist" className="btn-light">
                  <span>Launch AI Stylist</span>
                  <ArrowUpRight size={16} />
                </Link>
                <Link to="/recommendations" className="btn-outline-light">
                  <span>Browse Seasonal Edits</span>
                </Link>
              </div>
            </div>

            <div className="stylist-promo-preview">
              <div className="promo-chat-card">
                <span className="chat-card-kicker">SAMPLE DIALOGUE</span>
                <p className="chat-card-user">
                  “Curate a relaxed linen capsule for a weekend in Goa under ₹15,000.”
                </p>
                <div className="chat-card-reply">
                  <p>
                    “Pairing the <strong>Massimo Dutti Belgian Linen Overshirt</strong> in Sand with washed linen
                    drawstring trousers creates an effortless tonal silhouette...”
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
