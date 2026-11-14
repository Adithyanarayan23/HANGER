import React, { useState } from "react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import { Search, Sparkles, Menu, X, Compass } from "lucide-react";
import "../styles/navbar.css";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const closeMenu = () => setMobileMenuOpen(false);

  const handleCategoriesJump = (e) => {
    closeMenu();
    if (window.location.pathname === "/") {
      e.preventDefault();
      const el = document.getElementById("categories-section");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className="navbar-header">
      <div className="navbar-announcement">
        <span>ARCHIVE CURATION 2026 — UNIFIED LUXURY & HIGH-STREET DISCOVERY ACROSS INDIA</span>
      </div>
      <nav className="navbar-container">
        <div className="navbar-left">
          <button
            className="navbar-mobile-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link to="/" className="navbar-brand" onClick={closeMenu}>
            <span className="brand-logo-text">HANGER</span>
            <span className="brand-sub-tag">ATELIER</span>
          </Link>
        </div>

        <ul className={`navbar-links ${mobileMenuOpen ? "open" : ""}`}>
          <li>
            <NavLink to="/" end onClick={closeMenu} className={({ isActive }) => (isActive ? "active" : "")}>
              Discover
            </NavLink>
          </li>
          <li>
            <Link to="/#categories-section" onClick={handleCategoriesJump}>
              Categories
            </Link>
          </li>
          <li>
            <NavLink to="/recommendations" onClick={closeMenu} className={({ isActive }) => (isActive ? "active" : "")}>
              Recommendations
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/stylist"
              onClick={closeMenu}
              className={({ isActive }) => `stylist-nav-pill ${isActive ? "active" : ""}`}
            >
              <Sparkles size={14} />
              <span>AI Stylist</span>
            </NavLink>
          </li>
        </ul>

        <div className="navbar-actions">
          <button
            className="navbar-icon-btn"
            onClick={() => {
              closeMenu();
              navigate("/search");
            }}
            title="Search Catalog"
          >
            <Search size={18} />
            <span className="action-label">Search</span>
          </button>
          <Link to="/recommendations" className="navbar-icon-btn hide-mobile" title="Curated Edits">
            <Compass size={18} />
            <span className="action-label">Edits</span>
          </Link>
        </div>
      </nav>
    </header>
  );
}
