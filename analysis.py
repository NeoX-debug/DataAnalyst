import math
from database import get_db

def get_kpis():
    conn = get_db()
    c = conn.cursor()
    kpis = {
        "total_products":     c.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "total_competitors":  c.execute("SELECT COUNT(DISTINCT competitor) FROM prices").fetchone()[0],
        "total_reviews":      c.execute("SELECT COALESCE(SUM(review_count),0) FROM reviews").fetchone()[0],
        "avg_rating":         round(c.execute("SELECT COALESCE(AVG(stars),0) FROM reviews").fetchone()[0], 2),
        "total_price_entries":c.execute("SELECT COUNT(*) FROM prices").fetchone()[0],
    }
    conn.close()
    return kpis

def get_product_stats():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.id, p.name, p.category, p.brand,
               MIN(pr.price) as min_price,
               MAX(pr.price) as max_price,
               AVG(pr.price) as avg_price,
               COUNT(DISTINCT pr.competitor) as competitor_count,
               AVG(r.stars) as avg_stars,
               SUM(r.review_count) as total_reviews
        FROM products p
        LEFT JOIN prices pr ON p.id = pr.product_id
        LEFT JOIN reviews r  ON p.id = r.product_id
        GROUP BY p.id
        ORDER BY avg_stars DESC
    """).fetchall()

    stats = []
    for row in rows:
        # Compute price std dev via variance query
        prices = [x[0] for x in c.execute("SELECT price FROM prices WHERE product_id=?", (row["id"],)).fetchall()]
        if len(prices) > 1:
            mean = sum(prices) / len(prices)
            variance = sum((p - mean) ** 2 for p in prices) / len(prices)
            price_std = round(math.sqrt(variance), 2)
        else:
            price_std = 0.0

        stats.append({
            "id":               row["id"],
            "name":             row["name"],
            "category":         row["category"],
            "brand":            row["brand"],
            "min_price":        round(row["min_price"] or 0, 2),
            "max_price":        round(row["max_price"] or 0, 2),
            "avg_price":        round(row["avg_price"] or 0, 2),
            "price_std":        price_std,
            "price_range":      round((row["max_price"] or 0) - (row["min_price"] or 0), 2),
            "competitor_count": row["competitor_count"] or 0,
            "avg_stars":        round(row["avg_stars"] or 0, 2),
            "total_reviews":    int(row["total_reviews"] or 0),
        })
    conn.close()
    return stats

def get_competitor_prices():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.name as product_name, pr.competitor, ROUND(AVG(pr.price),2) as avg_price
        FROM products p JOIN prices pr ON p.id = pr.product_id
        GROUP BY p.id, pr.competitor
        ORDER BY p.name, pr.competitor
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_ratings_distribution():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT
          CASE
            WHEN stars >= 4.5 THEN '⭐ 4.5 - 5.0'
            WHEN stars >= 4.0 THEN '⭐ 4.0 - 4.5'
            WHEN stars >= 3.5 THEN '⭐ 3.5 - 4.0'
            WHEN stars >= 3.0 THEN '⭐ 3.0 - 3.5'
            ELSE '⭐ < 3.0'
          END as range_label,
          COUNT(*) as count
        FROM reviews
        GROUP BY range_label
        ORDER BY range_label DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_top_products(limit=5):
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.name, p.brand, p.category,
               ROUND(AVG(r.stars),2)        as avg_stars,
               SUM(r.review_count)          as total_reviews,
               ROUND(AVG(pr.price),2)       as avg_price
        FROM products p
        JOIN reviews r  ON p.id = r.product_id
        JOIN prices pr  ON p.id = pr.product_id
        GROUP BY p.id
        ORDER BY avg_stars DESC, total_reviews DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_price_by_category():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.category,
               ROUND(AVG(pr.price),2) as avg_price,
               ROUND(MIN(pr.price),2) as min_price,
               ROUND(MAX(pr.price),2) as max_price,
               COUNT(DISTINCT p.id)   as product_count
        FROM products p JOIN prices pr ON p.id = pr.product_id
        GROUP BY p.category
        ORDER BY avg_price DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_competitor_avg_prices():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT competitor,
               ROUND(AVG(price),2) as avg_price,
               ROUND(MIN(price),2) as min_price,
               ROUND(MAX(price),2) as max_price,
               COUNT(*) as entry_count
        FROM prices GROUP BY competitor ORDER BY avg_price ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def export_data():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.name, p.category, p.brand,
               pr.competitor, pr.price, pr.date_collected,
               r.stars, r.review_count, r.source
        FROM products p
        LEFT JOIN prices pr  ON p.id = pr.product_id
        LEFT JOIN reviews r  ON p.id = r.product_id
        ORDER BY p.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
