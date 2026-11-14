import React, { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import FilterSidebar from "../components/FilterSidebar";
import ProductGrid from "../components/ProductGrid";
import { PRODUCTS } from "../data/products";
import { useProductFilters } from "../hooks/useProductFilters";
import "../styles/products.css";

export default function SearchResults() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const initialCategory = searchParams.get("category") || "All";

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
  } = useProductFilters(PRODUCTS, initialCategory, initialQuery);

  useEffect(() => {
    const qParam = searchParams.get("q");
    const catParam = searchParams.get("category");
    if (qParam !== null) setSearchQuery(qParam);
    if (catParam !== null) setSelectedCategory(catParam);
  }, [searchParams, setSearchQuery, setSelectedCategory]);

  const handleSearchSubmit = (val) => {
    setSearchQuery(val);
    const params = {};
    if (val) params.q = val;
    if (selectedCategory !== "All") params.category = selectedCategory;
    setSearchParams(params);
  };

  return (
    <div className="search-page">
      <div className="search-page-header">
        <div className="section-container">
          <span className="section-kicker">ARCHIVE INDEX & DISCOVERY</span>
          <h1 className="page-hero-title">Search the Curated Catalog</h1>
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSubmit={handleSearchSubmit}
            onSuggestionClick={(suggestion) => handleSearchSubmit(suggestion)}
            showSuggestions={true}
          />
        </div>
      </div>

      <div className="section-container search-layout">
        <FilterSidebar
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          brands={brands}
          selectedBrand={selectedBrand}
          onSelectBrand={setSelectedBrand}
          colors={colors}
          selectedColor={selectedColor}
          onSelectColor={setSelectedColor}
          priceRange={priceRange}
          onSelectPriceRange={setPriceRange}
          activeFilterCount={activeFilterCount}
          onReset={() => {
            resetFilters();
            setSearchParams({});
          }}
        />

        <div className="search-results-main">
          <div className="search-results-topbar">
            <p className="results-summary-text">
              Showing <strong>{filteredProducts.length}</strong>{" "}
              {filteredProducts.length === 1 ? "piece" : "pieces"}
              {searchQuery ? ` for “${searchQuery}”` : ""}
              {selectedCategory !== "All" ? ` in ${selectedCategory}` : ""}
            </p>

            <div className="search-sort-box">
              <label htmlFor="search-sort-select">Sort by:</label>
              <select
                id="search-sort-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="featured">Editorial Featured</option>
                <option value="price-asc">Price: Low to High</option>
                <option value="price-desc">Price: High to Low</option>
                <option value="brand-asc">Brand: A – Z</option>
              </select>
            </div>
          </div>

          <ProductGrid
            products={filteredProducts}
            onResetFilters={() => {
              resetFilters();
              setSearchParams({});
            }}
            emptyMessage="No archival pieces matched your search criteria. Try clearing a filter or searching by fabric, color, or brand."
          />
        </div>
      </div>
    </div>
  );
}
