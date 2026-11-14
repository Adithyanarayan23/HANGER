import { useMemo, useState } from "react";

export function useProductFilters(products, initialCategory = "All", initialQuery = "") {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [selectedBrand, setSelectedBrand] = useState("All");
  const [selectedColor, setSelectedColor] = useState("All");
  const [priceRange, setPriceRange] = useState("ALL");
  const [sortBy, setSortBy] = useState("featured");

  const brands = useMemo(() => {
    const unique = Array.from(new Set(products.map((p) => p.brand)));
    return ["All", ...unique.sort()];
  }, [products]);

  const colors = useMemo(() => {
    const unique = Array.from(new Set(products.map((p) => p.color)));
    return ["All", ...unique.sort()];
  }, [products]);

  const categories = useMemo(() => {
    const unique = Array.from(new Set(products.map((p) => p.category)));
    return ["All", ...unique];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products
      .filter((product) => {
        if (selectedCategory !== "All" && product.category !== selectedCategory) {
          return false;
        }
        if (selectedBrand !== "All" && product.brand !== selectedBrand) {
          return false;
        }
        if (selectedColor !== "All" && product.color !== selectedColor) {
          return false;
        }
        if (priceRange === "UNDER_5000" && product.price >= 5000) {
          return false;
        }
        if (priceRange === "5000_10000" && (product.price < 5000 || product.price > 10000)) {
          return false;
        }
        if (priceRange === "ABOVE_10000" && product.price <= 10000) {
          return false;
        }
        if (searchQuery.trim() !== "") {
          const q = searchQuery.toLowerCase().trim();
          const searchable = [
            product.name,
            product.brand,
            product.category,
            product.color,
            product.sourceStore,
            product.collection,
            product.fabric,
            product.description
          ]
            .join(" ")
            .toLowerCase();

          // Support both multi-word natural language queries and direct keyword matches
          const stopWords = ["in", "for", "with", "under", "and", "the", "a", "an", "to", "of"];
          const tokens = q
            .replace(/[^\w\s₹]/g, "")
            .split(/\s+/)
            .filter((word) => word.length > 1 && !stopWords.includes(word) && !word.startsWith("₹"));

          if (searchable.includes(q)) {
            return true;
          }
          if (tokens.length > 0) {
            return tokens.some((token) => searchable.includes(token));
          }
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "price-asc") return a.price - b.price;
        if (sortBy === "price-desc") return b.price - a.price;
        if (sortBy === "brand-asc") return a.brand.localeCompare(b.brand);
        return (b.trending ? 1 : 0) - (a.trending ? 1 : 0);
      });
  }, [products, selectedCategory, selectedBrand, selectedColor, priceRange, sortBy, searchQuery]);

  const resetFilters = () => {
    setSearchQuery("");
    setSelectedCategory("All");
    setSelectedBrand("All");
    setSelectedColor("All");
    setPriceRange("ALL");
    setSortBy("featured");
  };

  const activeFilterCount =
    (selectedCategory !== "All" ? 1 : 0) +
    (selectedBrand !== "All" ? 1 : 0) +
    (selectedColor !== "All" ? 1 : 0) +
    (priceRange !== "ALL" ? 1 : 0) +
    (searchQuery.trim() !== "" ? 1 : 0);

  return {
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
  };
}
