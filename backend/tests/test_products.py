import json
import urllib.error
import urllib.parse
import urllib.request
from sqlalchemy.orm import sessionmaker

from app.database.connection import engine
from app.models.product import Product


def req(method: str, url: str, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def run_live_crud_verification(base_url: str = "http://localhost:8000/api/v1/products"):
    # 1. Create product 1 (HTTP 201)
    p1_data = {
        "name": "Relaxed Belgian Linen Overshirt",
        "description": "100% European flax linen unlined overshirt.",
        "brand": "Massimo Dutti",
        "category": "Outerwear",
        "subcategory": "Overshirts",
        "color": "Sand",
        "price": "7490.00",
        "original_price": "9990.00",
        "currency": "INR",
        "sizes": ["S", "M", "L", "XL"],
        "image_urls": ["https://images.unsplash.com/photo-1591047139829-d91aecb6caea"],
        "is_available": True,
        "source_website": "Ajio Luxe",
        "source_product_id": "AJIO-MD-001",
        "product_url": "https://luxe.ajio.com/product/md-001",
    }
    status1, p1 = req("POST", f"{base_url}/", p1_data)
    p1_id = p1["id"]
    print(f"[1] Create Product 1 -> HTTP {status1} | id={p1_id}, price={p1['price']}, sizes={p1['sizes']}")
    assert status1 == 201

    # Create product 2 (HTTP 201)
    p2_data = {
        "name": "Pleated Wide-Leg Tailored Trousers",
        "description": "Recycled wool and Tencel blend trousers.",
        "brand": "COS",
        "category": "Bottomwear",
        "subcategory": "Trousers",
        "color": "Charcoal",
        "price": "6890.00",
        "original_price": "6890.00",
        "sizes": ["30", "32", "34"],
        "image_urls": ["https://images.unsplash.com/photo-1594633312681-425c7b97ccd1"],
        "is_available": True,
        "source_website": "Myntra",
        "source_product_id": "MYN-COS-002",
        "product_url": "https://www.myntra.com/trousers/cos-002",
    }
    status2, p2 = req("POST", f"{base_url}/", p2_data)
    p2_id = p2["id"]
    print(f"[1b] Create Product 2 -> HTTP {status2} | id={p2_id}, brand={p2['brand']}")
    assert status2 == 201

    # Verify rows actually exist inside PostgreSQL hanger_db
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db_row = db.get(Product, p1_id)
        assert db_row is not None and db_row.name == "Relaxed Belgian Linen Overshirt"
        print(f"[DB Check] Verified Product id={p1_id} persisted in PostgreSQL table 'products'")

    # 2. Retrieve all products
    st_all, all_prods = req("GET", f"{base_url}/")
    print(f"[2] Get All Products -> HTTP {st_all} | count={len(all_prods)}")
    assert st_all == 200 and len(all_prods) >= 2

    # 3. Retrieve one product by ID
    st_one, one_prod = req("GET", f"{base_url}/{p1_id}")
    print(f"[3] Get Product by ID ({p1_id}) -> HTTP {st_one} | name='{one_prod['name']}'")
    assert st_one == 200 and one_prod["id"] == p1_id

    # 4. Search by product name
    st_srch, srch = req("GET", f"{base_url}/?search=Belgian")
    print(f"[4] Search by Name ('Belgian') -> HTTP {st_srch} | matches={len(srch)}")
    assert st_srch == 200 and any(x["id"] == p1_id for x in srch)

    # 5. Filter by category
    st_cat, cat = req("GET", f"{base_url}/?category=Bottomwear")
    print(f"[5] Filter by Category ('Bottomwear') -> HTTP {st_cat} | matches={len(cat)}")
    assert st_cat == 200 and all(x["category"] == "Bottomwear" for x in cat)

    # 6. Filter by brand
    st_br, br = req("GET", f"{base_url}/?brand=COS")
    print(f"[6] Filter by Brand ('COS') -> HTTP {st_br} | matches={len(br)}")
    assert st_br == 200 and all(x["brand"] == "COS" for x in br)

    # 7. Filter by colour
    st_col, col = req("GET", f"{base_url}/?color=Sand")
    print(f"[7] Filter by Color ('Sand') -> HTTP {st_col} | matches={len(col)}")
    assert st_col == 200 and all(x["color"] == "Sand" for x in col)

    # 8. Filter by price range
    st_pr, pr = req("GET", f"{base_url}/?min_price=7000&max_price=8000")
    print(f"[8] Filter by Price Range (7000-8000) -> HTTP {st_pr} | matches={len(pr)}")
    assert st_pr == 200 and any(x["id"] == p1_id for x in pr)

    # Invalid price range (min_price > max_price -> HTTP 400)
    st_bad_pr, _ = req("GET", f"{base_url}/?min_price=9000&max_price=5000")
    print(f"[8b] Invalid Price Range (9000 > 5000) -> HTTP {st_bad_pr}")
    assert st_bad_pr == 400

    # 9. Pagination
    st_pg, pg = req("GET", f"{base_url}/?skip=0&limit=1")
    print(f"[9] Pagination (skip=0, limit=1) -> HTTP {st_pg} | returned={len(pg)}")
    assert st_pg == 200 and len(pg) == 1

    # 10. Update a product (PATCH)
    st_up, up = req("PATCH", f"{base_url}/{p1_id}", {"price": "6990.00", "color": "Warm Sand"})
    print(f"[10] PATCH Product {p1_id} -> HTTP {st_up} | new_price={up['price']}, new_color='{up['color']}'")
    assert st_up == 200 and up["price"] == "6990.00" and up["color"] == "Warm Sand"

    # 14. Duplicate source product handling (HTTP 409)
    st_dup, dup = req("POST", f"{base_url}/", p1_data)
    print(f"[14] Duplicate Source Product -> HTTP {st_dup} | detail='{dup['detail']}'")
    assert st_dup == 409

    # 11. Delete products
    st_del2, del2 = req("DELETE", f"{base_url}/{p2_id}")
    print(f"[11] DELETE Product {p2_id} -> HTTP {st_del2} | {del2}")
    assert st_del2 == 200
    st_del1, _ = req("DELETE", f"{base_url}/{p1_id}")
    assert st_del1 == 200

    # 12. Request nonexistent product (HTTP 404)
    st_404_get, err404 = req("GET", f"{base_url}/{p2_id}")
    st_404_patch, _ = req("PATCH", f"{base_url}/{p2_id}", {"price": "5000.00"})
    st_404_del, _ = req("DELETE", f"{base_url}/{p2_id}")
    print(f"[12] Nonexistent Product ({p2_id}) -> GET:{st_404_get}, PATCH:{st_404_patch}, DELETE:{st_404_del} | '{err404['detail']}'")
    assert st_404_get == 404 and st_404_patch == 404 and st_404_del == 404

    # 13. Submit invalid product data (HTTP 422)
    bad_payload = dict(p1_data, price="-500.00", product_url="not-a-url", name="   ")
    st_422, err422 = req("POST", f"{base_url}/", bad_payload)
    print(f"[13] Invalid Product Data -> HTTP {st_422} | validation_errors={len(err422['detail'])}")
    assert st_422 == 422

    # Check Swagger UI
    with urllib.request.urlopen("http://localhost:8000/docs") as docs_resp:
        print(f"[Swagger] GET http://localhost:8000/docs -> HTTP {docs_resp.status}")
        assert docs_resp.status == 200

    print("\nALL 14 PHASE 3 PRODUCT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_live_crud_verification()
