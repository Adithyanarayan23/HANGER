import { PRODUCTS } from "../data/products";

export const SUGGESTED_PROMPTS = [
  "Curate a linen capsule wardrobe for a coastal weekend in Goa",
  "Suggest an understated gallery opening outfit in monochrome tones",
  "Find relaxed tailored workwear pieces under ₹8,000",
  "Pair shoes and accessories with the Ivory Mulberry Silk Slip Dress"
];

export const INITIAL_CONVERSATIONS = [
  {
    id: "conv-1",
    title: "Coastal Linen Capsule",
    updatedAt: "Today",
    messages: [
      {
        id: "msg-welcome",
        sender: "assistant",
        timestamp: "Just now",
        text: "Welcome to the HANGER Editorial Atelier. Share an occasion, aesthetic, palette, or budget—and I will curate pieces across India's finest fashion houses and concept stores.",
        recommendations: ["hng-001", "hng-002", "hng-006"]
      }
    ]
  },
  {
    id: "conv-2",
    title: "Monochrome Gallery Evening",
    updatedAt: "Yesterday",
    messages: [
      {
        id: "msg-prev-1",
        sender: "user",
        timestamp: "Yesterday",
        text: "Suggest an understated gallery opening outfit in monochrome tones"
      },
      {
        id: "msg-prev-2",
        sender: "assistant",
        timestamp: "Yesterday",
        text: "For an evening gallery opening, I recommend pairing fluid charcoal wool-lyocell tailoring with crisp organic poplin shirting and hand-welted black box calfskin loafers. The silhouette balances volume at the trouser leg with structured waist definition.",
        stylistNote: "Tuck the asymmetric tie-waist shirt loosely and leave the cuffs unbuttoned for an effortless editorial finish.",
        recommendations: ["hng-002", "hng-013", "hng-005"]
      }
    ]
  }
];

/**
 * Frontend demonstration service for the HANGER AI Stylist.
 * Uses local mock product catalog and curated response templates.
 * Isolated in its own service module so a backend LLM/RAG API can be wired in later.
 */
export function generateStylistReply(userInput) {
  const q = userInput.toLowerCase();

  if (q.includes("linen") || q.includes("coastal") || q.includes("goa") || q.includes("summer") || q.includes("resort")) {
    const recs = PRODUCTS.filter((p) => ["hng-001", "hng-014", "hng-010", "hng-012"].includes(p.id));
    return {
      text: "For a breathable coastal capsule, start with European flax linen in warm sand tones. Pairing the Massimo Dutti Belgian Linen Overshirt over relaxed drawstring linen trousers creates a tonal column silhouette, grounded by Veja suede court sneakers and Italian tortoise acetate eyewear.",
      stylistNote: "Roll the overshirt sleeves twice and wear it unfastened over a lightweight tank or bare collarbone.",
      products: recs
    };
  }

  if (q.includes("gallery") || q.includes("monochrome") || q.includes("black") || q.includes("charcoal") || q.includes("minimal")) {
    const recs = PRODUCTS.filter((p) => ["hng-002", "hng-013", "hng-005", "hng-009"].includes(p.id));
    return {
      text: "A monochrome architectural palette relies on contrasting textures rather than loud color. Here is an edit combining COS double-pleated wool-lyocell trousers, crisp organic cotton poplin, and Goodyear-welted French box calfskin loafers.",
      stylistNote: "Contrast matte wool with polished calfskin leather to give dark tonal outfits visual depth.",
      products: recs
    };
  }

  if (q.includes("under") || q.includes("budget") || q.includes("8,000") || q.includes("8000") || q.includes("workwear") || q.includes("office")) {
    const recs = PRODUCTS.filter((p) => p.price <= 8000).slice(0, 4);
    return {
      text: "Here is an edit of elevated workwear and foundational wardrobe staples under ₹8,000—featuring pleated tailored trousers, fine Australian merino knitwear, and sculpted nappa leather accessories.",
      stylistNote: "Investing in extra-fine merino and pleated wool blends gives high-street pieces a luxury tailored drape.",
      products: recs
    };
  }

  if (q.includes("evening") || q.includes("silk") || q.includes("dress") || q.includes("party") || q.includes("dinner") || q.includes("festive")) {
    const recs = PRODUCTS.filter((p) => ["hng-003", "hng-011", "hng-007", "hng-006"].includes(p.id));
    return {
      text: "For evening and celebratory dressing, luminous natural silk and structured outerwear create timeless drama. Consider the bias-cut Mulberry Silk Midi Slip layered beneath the H&M Studio olive wool trench, or the handwoven Chanderi silk ensemble from Nicobar.",
      stylistNote: "Drape the structured trench over your shoulders without using the sleeves to frame the cowl neckline.",
      products: recs
    };
  }

  // Fallback keyword matching across product catalog
  const matched = PRODUCTS.filter(
    (p) =>
      q.includes(p.category.toLowerCase()) ||
      q.includes(p.color.toLowerCase()) ||
      q.includes(p.brand.toLowerCase()) ||
      p.name.toLowerCase().split(" ").some((word) => word.length > 3 && q.includes(word))
  ).slice(0, 3);

  const fallbackProducts = matched.length > 0 ? matched : PRODUCTS.slice(0, 3);

  return {
    text: `Based on your note ("${userInput}"), I have selected ${fallbackProducts.length} pieces from our current seasonal archive that emphasize clean proportions, natural textiles, and versatile earth-and-mineral palettes.`,
    stylistNote: "Focus on one relaxed volume piece balanced by a structured anchor (such as welted footwear or a geometric shoulder bag).",
    products: fallbackProducts
  };
}
