import React from "react";
import ProductCard from "./ProductCard";
import { RotateCcw } from "lucide-react";

export default function ProductGrid({ products, onResetFilters, emptyMessage }) {
  if (!products || products.length === 0) {
    return (
      <div className="empty-grid-state">
        <p className="empty-eyebrow">ARCHIVE QUERY</p>
        <h3 className="empty-title">No pieces match your current selection</h3>
        <p className="empty-subtitle">
          {emptyMessage ||
            "Try broadening your price filter, switching color palettes, or resetting all active filters."}
        </p>
        {onResetFilters && (
          <button type="button" className="btn-secondary" onClick={onResetFilters}>
            <RotateCcw size={15} />
            <span>Reset All Filters</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
