import io
import csv
from flask import Flask, render_template, request, jsonify, Response
from database import init_db, seed_demo_data, get_db
import analysis
import classifier

app = Flask(__name__)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
seed_demo_data()

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/collect")
def collect():
    return render_template("collect.html")

@app.route("/analysis")
def analysis_page():
    return render_template("analysis.html")

@app.route("/classify")
def classify_page():
    return render_template("classify.html")

# ── API : collecte ─────────────────────────────────────────────────────────────
@app.route("/api/product", methods=["POST"])
def add_product():
    data = request.get_json()
    name     = data.get("name", "").strip()
    category = data.get("category", "").strip()
    brand    = data.get("brand", "").strip()
    if not name or not category or not brand:
        return jsonify({"error": "Nom, catégorie et marque sont requis"}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO products (name, category, brand) VALUES (?,?,?)", (name, category, brand))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"product_id": pid, "message": f"Produit '{name}' ajouté (id={pid})"}), 201

@app.route("/api/price", methods=["POST"])
def add_price():
    data = request.get_json()
    pid        = data.get("product_id")
    competitor = data.get("competitor", "").strip()
    price      = data.get("price")
    if not pid or not competitor or price is None:
        return jsonify({"error": "product_id, competitor et price requis"}), 400
    try:
        price = float(price)
    except ValueError:
        return jsonify({"error": "Prix invalide"}), 400
    conn = get_db()
    conn.execute("INSERT INTO prices (product_id, competitor, price) VALUES (?,?,?)", (pid, competitor, price))
    conn.commit()
    conn.close()
    return jsonify({"message": "Prix ajouté"}), 201

@app.route("/api/review", methods=["POST"])
def add_review():
    data = request.get_json()
    pid    = data.get("product_id")
    stars  = data.get("stars")
    count  = data.get("review_count", 0)
    source = data.get("source", "Manuel").strip()
    if not pid or stars is None:
        return jsonify({"error": "product_id et stars requis"}), 400
    try:
        stars = float(stars)
        count = int(count)
        if not (1 <= stars <= 5):
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Stars doit être entre 1 et 5"}), 400
    conn = get_db()
    conn.execute("INSERT INTO reviews (product_id, stars, review_count, source) VALUES (?,?,?,?)",
                 (pid, stars, count, source))
    conn.commit()
    conn.close()
    return jsonify({"message": "Avis ajouté"}), 201

@app.route("/api/spec", methods=["POST"])
def add_spec():
    data = request.get_json()
    pid = data.get("product_id")
    key = data.get("spec_key", "").strip()
    val = data.get("spec_value", "").strip()
    if not pid or not key or not val:
        return jsonify({"error": "product_id, spec_key et spec_value requis"}), 400
    conn = get_db()
    conn.execute("INSERT INTO specs (product_id, spec_key, spec_value) VALUES (?,?,?)", (pid, key, val))
    conn.commit()
    conn.close()
    return jsonify({"message": "Caractéristique ajoutée"}), 201

@app.route("/api/product/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Produit supprimé"}), 200

# ── API : analyse ──────────────────────────────────────────────────────────────
@app.route("/api/kpis")
def api_kpis():
    return jsonify(analysis.get_kpis())

@app.route("/api/products")
def api_products():
    return jsonify(analysis.get_product_stats())

@app.route("/api/competitor-prices")
def api_competitor_prices():
    return jsonify(analysis.get_competitor_prices())

@app.route("/api/ratings-distribution")
def api_ratings():
    return jsonify(analysis.get_ratings_distribution())

@app.route("/api/top-products")
def api_top_products():
    n = request.args.get("limit", 5, type=int)
    return jsonify(analysis.get_top_products(n))

@app.route("/api/price-by-category")
def api_price_category():
    return jsonify(analysis.get_price_by_category())

@app.route("/api/competitor-avg")
def api_competitor_avg():
    return jsonify(analysis.get_competitor_avg_prices())

@app.route("/api/export-csv")
def export_csv():
    rows = analysis.export_data()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["Produit","Catégorie","Marque","Concurrent","Prix","Date","Étoiles","Nb Avis","Source"])
    for r in rows:
        writer.writerow([r.get(k,"") for k in
            ["name","category","brand","competitor","price","date_collected","stars","review_count","source"]])
    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return output

# ── API : classification ───────────────────────────────────────────────────────
@app.route("/api/train", methods=["POST"])
def api_train():
    result = classifier.train()
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data        = request.get_json()
    avg_stars   = float(data.get("avg_stars", 0))
    reviews     = float(data.get("total_reviews", 0))
    avg_price   = float(data.get("avg_price", 0))
    price_std   = float(data.get("price_std", 0))
    competitors = float(data.get("competitor_count", 1))
    result = classifier.predict_one(avg_stars, reviews, avg_price, price_std, competitors)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route("/api/predictions")
def api_predictions():
    return jsonify(classifier.get_all_predictions())

@app.route("/api/metrics")
def api_metrics():
    m = classifier.get_metrics()
    if not m:
        return jsonify({"error": "Modèle non encore entraîné"}), 404
    return jsonify(m)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
