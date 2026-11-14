import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowUpRight,
  Sparkles,
  Check,
  ShieldCheck,
  Layers,
  Tag
} from "lucide-react";
import { PRODUCTS, formatINR } from "../data/products";
import ProductGrid from "../components/ProductGrid";
import "../styles/products.css";

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const product = PRODUCTS.find((p) => p.id === id);
  const [activeImage, setActiveImage] = useState(product ? product.image : "");
  const [selectedSize, setSelectedSize] = useState(
    product && product.sizes && product.sizes.length > 0 ? product.sizes[0] : "M"
  );

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (product) {
      setActiveImage(product.image);
      setSelectedSize(product.sizes?.[0] || "M");
    }
  }, [id, product]);

  if (!product) {
    return (
      <div className="section-container product-not-found">
        <span className="section-kicker">404 ARCHIVE ENTRY</span>
        <h2>Piece Not Found in Current Edit</h2>
        <p>The garment you are looking for may have been rotated out of our seasonal catalog.</p>
        <Link to="/search" className="btn-primary">
          <span>Return to Archive</span>
        </Link>
      </div>
    );
  }

  const galleryImages =
    product.gallery && product.gallery.length > 0 ? product.gallery : [product.image];

  const relatedProducts = PRODUCTS.filter(
    (p) => p.id !== product.id && (p.category === product.category || p.collection === product.collection)
  ).slice(0, 4);

  const hasDiscount = product.originalPrice && product.originalPrice > product.price;
  const discountPercent = hasDiscount
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  return (
    <div className="product-details-page">
      <div className="section-container">
        {/* Breadcrumb & Back */}
        <div className="pdp-breadcrumb-bar">
          <button type="button" className="back-link-btn" onClick={() => navigate(-1)}>
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>
          <div className="breadcrumb-trail">
            <Link to="/">Archive</Link>
            <span>/</span>
            <Link to={`/search?category=${encodeURIComponent(product.category)}`}>
              {product.category}
            </Link>
            <span>/</span>
            <span className="current-crumb">{product.name}</span>
          </div>
        </div>

        {/* Main PDP Two-Column Layout */}
        <div className="pdp-main-grid">
          {/* Gallery Column */}
          <div className="pdp-gallery">
            <div className="pdp-thumbnails">
              {galleryImages.map((imgUrl, index) => (
                <button
                  key={index}
                  type="button"
                  className={`pdp-thumb-btn ${activeImage === imgUrl ? "active" : ""}`}
                  onClick={() => setActiveImage(imgUrl)}
                >
                  <img src={imgUrl} alt={`${product.name} view ${index + 1}`} />
                </button>
              ))}
            </div>
            <div className="pdp-primary-image-wrap">
              <img src={activeImage} alt={product.name} className="pdp-primary-image" />
              <span className="pdp-collection-badge">{product.collection}</span>
            </div>
          </div>

          {/* Information Column */}
          <div className="pdp-info">
            <div className="pdp-brand-row">
              <span className="pdp-brand">{product.brand}</span>
              <span className="pdp-store-pill">Available on {product.sourceStore}</span>
            </div>

            <h1 className="pdp-title">{product.name}</h1>

            <div className="pdp-price-row">
              <span className="pdp-price">{formatINR(product.price)}</span>
              {hasDiscount && (
                <>
                  <span className="pdp-original-price">{formatINR(product.originalPrice)}</span>
                  <span className="pdp-discount-tag">{discountPercent}% OFF</span>
                </>
              )}
            </div>

            <p className="pdp-description">{product.description}</p>

            {/* Color & Category Attributes */}
            <div className="pdp-attributes-grid">
              <div className="pdp-attr-box">
                <span className="attr-label">Color Palette</span>
                <div className="attr-value-row">
                  <span
                    className="color-dot"
                    style={{ backgroundColor: product.colorHex || "#ccc" }}
                  />
                  <strong>{product.color}</strong>
                </div>
              </div>

              <div className="pdp-attr-box">
                <span className="attr-label">Category</span>
                <div className="attr-value-row">
                  <Tag size={14} />
                  <strong>{product.category}</strong>
                </div>
              </div>

              <div className="pdp-attr-box">
                <span className="attr-label">Source Partner</span>
                <div className="attr-value-row">
                  <ShieldCheck size={14} />
                  <strong>{product.sourceStore}</strong>
                </div>
              </div>
            </div>

            {/* Size Selector */}
            {product.sizes && (
              <div className="pdp-size-section">
                <div className="size-header">
                  <span>Select Size</span>
                  <span className="fit-note-inline">{product.fit}</span>
                </div>
                <div className="size-pills">
                  {product.sizes.map((sz) => (
                    <button
                      key={sz}
                      type="button"
                      className={`size-pill ${selectedSize === sz ? "active" : ""}`}
                      onClick={() => setSelectedSize(sz)}
                    >
                      {sz}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Primary Actions */}
            <div className="pdp-cta-row">
              <a
                href={product.storeUrl}
                target="_blank"
                rel="noreferrer"
                className="btn-primary pdp-visit-btn"
              >
                <span>Visit {product.sourceStore}</span>
                <ArrowUpRight size={18} />
              </a>

              <Link to="/stylist" className="btn-secondary pdp-stylist-btn">
                <Sparkles size={16} />
                <span>Style This Piece with AI</span>
              </Link>
            </div>

            {/* Editorial Highlights & Specifications */}
            <div className="pdp-specs-accordion">
              <div className="spec-block">
                <h4>
                  <Layers size={15} /> Architectural & Textile Notes
                </h4>
                <ul className="pdp-highlights-list">
                  {product.highlights?.map((item, idx) => (
                    <li key={idx}>
                      <Check size={14} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="spec-meta-rows">
                <div className="spec-row">
                  <span className="spec-key">Composition</span>
                  <span className="spec-val">{product.fabric}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-key">Silhouette & Fit</span>
                  <span className="spec-val">{product.fit}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-key">Garment Care</span>
                  <span className="spec-val">{product.care}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Related Products */}
        <section className="pdp-related-section">
          <div className="section-header-row">
            <div>
              <span className="section-kicker">COMPLEMENTARY ARCHIVE</span>
              <h2 className="section-title">Related Pieces & Pairings</h2>
            </div>
            <Link to="/search" className="section-link-arrow">
              <span>Explore All</span>
              <ArrowUpRight size={16} />
            </Link>
          </div>
          <ProductGrid products={relatedProducts} />
        </section>
      </div>
    </div>
  );
}
