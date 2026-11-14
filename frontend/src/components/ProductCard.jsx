import React from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { formatINR } from "../data/products";

export default function ProductCard({ product }) {
  const hasDiscount = product.originalPrice && product.originalPrice > product.price;

  return (
    <article className="product-card">
      <Link to={`/product/${product.id}`} className="product-image-link">
        <div className="product-image-container">
          <img src={product.image} alt={product.name} className="product-image" loading="lazy" />
          <div className="product-badges">
            <span className="badge-store">{product.sourceStore}</span>
            {product.trending && <span className="badge-trending">Editorial Pick</span>}
          </div>
          <div className="product-hover-overlay">
            <span className="hover-view-text">
              Inspect Piece <ArrowUpRight size={14} />
            </span>
          </div>
        </div>
      </Link>

      <div className="product-card-body">
        <div className="product-meta-top">
          <span className="product-brand">{product.brand}</span>
          <span className="product-category-tag">{product.category}</span>
        </div>

        <Link to={`/product/${product.id}`} className="product-title-link">
          <h3 className="product-title">{product.name}</h3>
        </Link>

        <div className="product-meta-bottom">
          <div className="product-price-group">
            <span className="product-price">{formatINR(product.price)}</span>
            {hasDiscount && (
              <span className="product-original-price">{formatINR(product.originalPrice)}</span>
            )}
          </div>

          <div className="product-color-indicator" title={`Color: ${product.color}`}>
            <span
              className="color-dot"
              style={{ backgroundColor: product.colorHex || "#ccc" }}
            />
            <span className="color-name">{product.color}</span>
          </div>
        </div>
      </div>
    </article>
  );
}
