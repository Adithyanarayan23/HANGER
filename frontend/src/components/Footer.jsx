import React from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-top">
          <div className="footer-brand-col">
            <Link to="/" className="footer-logo">
              HANGER
            </Link>
            <p className="footer-tagline">
              An AI-curated fashion discovery platform uniting architectural essentials, heritage Indian textiles, and
              contemporary luxury across premier stores.
            </p>
            <span className="footer-edition">EDITION 2026 • MUMBAI / NEW DELHI / BENGALURU</span>
          </div>

          <div className="footer-links-col">
            <h4>Navigation</h4>
            <ul>
              <li><Link to="/">Discover Archive</Link></li>
              <li><Link to="/search">Advanced Search</Link></li>
              <li><Link to="/recommendations">Curated Edits</Link></li>
              <li><Link to="/stylist">AI Personal Stylist</Link></li>
            </ul>
          </div>

          <div className="footer-links-col">
            <h4>Silhouettes</h4>
            <ul>
              <li><Link to="/search?category=Outerwear">Outerwear & Layers</Link></li>
              <li><Link to="/search?category=Topwear">Architectural Topwear</Link></li>
              <li><Link to="/search?category=Bottomwear">Tailored Bottomwear</Link></li>
              <li><Link to="/search?category=Dresses">Silk & Chanderi Dresses</Link></li>
              <li><Link to="/search?category=Footwear">Welted & Suede Footwear</Link></li>
            </ul>
          </div>

          <div className="footer-links-col">
            <h4>Partner Houses</h4>
            <ul>
              <li>
                <a href="https://luxe.ajio.com" target="_blank" rel="noreferrer">
                  Ajio Luxe <ArrowUpRight size={12} />
                </a>
              </li>
              <li>
                <a href="https://luxury.tatacliq.com" target="_blank" rel="noreferrer">
                  Tata CLiQ Luxury <ArrowUpRight size={12} />
                </a>
              </li>
              <li>
                <a href="https://www.myntra.com" target="_blank" rel="noreferrer">
                  Myntra <ArrowUpRight size={12} />
                </a>
              </li>
              <li>
                <a href="https://www.zara.com/in" target="_blank" rel="noreferrer">
                  Zara India <ArrowUpRight size={12} />
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} HANGER Fashion Intelligence. Frontend Editorial Prototype.</p>
          <p className="footer-note">Prices in INR (₹) • Sourced from partner catalogues.</p>
        </div>
      </div>
    </footer>
  );
}
