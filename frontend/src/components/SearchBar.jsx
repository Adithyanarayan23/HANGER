import React from "react";
import { Search, ArrowUpRight, X } from "lucide-react";
import { SEARCH_SUGGESTIONS } from "../data/products";

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  onSuggestionClick,
  placeholder = "Describe a mood, silhouette, fabric or occasion (e.g., 'Relaxed sand linen overshirt')...",
  showSuggestions = true
}) {
  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) onSubmit(value);
  };

  return (
    <div className="searchbar-wrapper">
      <form className="searchbar-form" onSubmit={handleFormSubmit}>
        <div className="searchbar-input-group">
          <Search size={20} className="searchbar-icon" />
          <input
            type="text"
            className="searchbar-input"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            aria-label="Natural language fashion search"
          />
          {value && (
            <button
              type="button"
              className="searchbar-clear-btn"
              onClick={() => onChange("")}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>
        <button type="submit" className="searchbar-submit-btn">
          <span>Search Edit</span>
          <ArrowUpRight size={16} />
        </button>
      </form>

      {showSuggestions && (
        <div className="search-suggestions-row">
          <span className="suggestions-label">Try asking:</span>
          <div className="suggestions-pills">
            {SEARCH_SUGGESTIONS.map((item) => (
              <button
                key={item}
                type="button"
                className="suggestion-pill"
                onClick={() => onSuggestionClick && onSuggestionClick(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
