import React from "react";
import { SlidersHorizontal, RotateCcw } from "lucide-react";

const PRICE_OPTIONS = [
  { id: "ALL", label: "All Price Tiers" },
  { id: "UNDER_5000", label: "Under ₹5,000" },
  { id: "5000_10000", label: "₹5,000 – ₹10,000" },
  { id: "ABOVE_10000", label: "Above ₹10,000" }
];

export default function FilterSidebar({
  categories,
  selectedCategory,
  onSelectCategory,
  brands,
  selectedBrand,
  onSelectBrand,
  colors,
  selectedColor,
  onSelectColor,
  priceRange,
  onSelectPriceRange,
  activeFilterCount,
  onReset
}) {
  return (
    <aside className="filter-sidebar">
      <div className="filter-sidebar-header">
        <div className="filter-title-row">
          <SlidersHorizontal size={16} />
          <span>Refine Archive</span>
        </div>
        {activeFilterCount > 0 && (
          <button type="button" className="filter-reset-link" onClick={onReset}>
            <RotateCcw size={13} />
            <span>Clear ({activeFilterCount})</span>
          </button>
        )}
      </div>

      {/* Category Filter */}
      <div className="filter-group">
        <h4 className="filter-group-title">Category</h4>
        <div className="filter-pill-list">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`filter-chip ${selectedCategory === cat ? "active" : ""}`}
              onClick={() => onSelectCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Price Range Filter */}
      <div className="filter-group">
        <h4 className="filter-group-title">Price Range (INR)</h4>
        <div className="filter-radio-list">
          {PRICE_OPTIONS.map((opt) => (
            <label key={opt.id} className="filter-radio-label">
              <input
                type="radio"
                name="priceRange"
                checked={priceRange === opt.id}
                onChange={() => onSelectPriceRange(opt.id)}
              />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Brand Filter */}
      <div className="filter-group">
        <h4 className="filter-group-title">Fashion House / Brand</h4>
        <div className="filter-pill-list">
          {brands.map((brand) => (
            <button
              key={brand}
              type="button"
              className={`filter-chip ${selectedBrand === brand ? "active" : ""}`}
              onClick={() => onSelectBrand(brand)}
            >
              {brand}
            </button>
          ))}
        </div>
      </div>

      {/* Color Filter */}
      <div className="filter-group">
        <h4 className="filter-group-title">Palette</h4>
        <div className="filter-pill-list">
          {colors.map((color) => (
            <button
              key={color}
              type="button"
              className={`filter-chip ${selectedColor === color ? "active" : ""}`}
              onClick={() => onSelectColor(color)}
            >
              {color}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
