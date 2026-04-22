import math
from database import get_db

try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

FEATURE_NAMES = ["avg_stars", "total_reviews", "avg_price", "price_std", "competitor_count"]
POPULAR_STARS = 4.0
POPULAR_REVIEWS = 50

_model = None
_last_metrics = {}

def _get_dataset():
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.id,
               COALESCE(AVG(r.stars), 0)        as avg_stars,
               COALESCE(SUM(r.review_count), 0)  as total_reviews,
               COALESCE(AVG(pr.price), 0)        as avg_price,
               COUNT(DISTINCT pr.competitor)      as competitor_count
        FROM products p
        LEFT JOIN reviews r  ON p.id = r.product_id
        LEFT JOIN prices pr  ON p.id = pr.product_id
        GROUP BY p.id
    """).fetchall()

    X, y = [], []
    for row in rows:
        prices = [x[0] for x in c.execute("SELECT price FROM prices WHERE product_id=?", (row["id"],)).fetchall()]
        if len(prices) > 1:
            mean = sum(prices) / len(prices)
            price_std = math.sqrt(sum((p - mean)**2 for p in prices) / len(prices))
        else:
            price_std = 0.0

        avg_stars    = float(row["avg_stars"])
        total_reviews= float(row["total_reviews"])
        avg_price    = float(row["avg_price"])
        comp_count   = float(row["competitor_count"])

        label = 1 if (avg_stars >= POPULAR_STARS and total_reviews >= POPULAR_REVIEWS) else 0
        X.append([avg_stars, total_reviews, avg_price, price_std, comp_count])
        y.append(label)

    conn.close()
    return X, y

def train():
    global _model, _last_metrics
    if not SKLEARN_OK:
        return {"error": "scikit-learn n'est pas installé. Exécutez : pip install scikit-learn"}

    X, y = _get_dataset()
    if len(X) < 2:
        return {"error": "Données insuffisantes (minimum 2 produits avec prix et avis)."}

    X_np = np.array(X, dtype=float)
    y_np = np.array(y, dtype=int)

    if len(X) >= 6:
        X_tr, X_te, y_tr, y_te = train_test_split(X_np, y_np, test_size=0.25, random_state=42, stratify=y_np if len(set(y_np)) > 1 else None)
    else:
        X_tr, X_te, y_tr, y_te = X_np, X_np, y_np, y_np

    _model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    _model.fit(X_tr, y_tr)

    y_pred = _model.predict(X_te)
    acc = accuracy_score(y_te, y_pred)

    if len(X) >= 5 and len(set(y_np)) > 1:
        cv = cross_val_score(_model, X_np, y_np, cv=min(5, len(X)), scoring="accuracy")
        cv_mean, cv_std = float(cv.mean()), float(cv.std())
    else:
        cv_mean, cv_std = acc, 0.0

    cm = confusion_matrix(y_te, y_pred, labels=[0, 1]).tolist()
    report = classification_report(y_te, y_pred, target_names=["Non-populaire", "Populaire"],
                                   output_dict=True, zero_division=0)
    importances = {n: round(float(v), 4) for n, v in zip(FEATURE_NAMES, _model.feature_importances_)}

    _last_metrics = {
        "accuracy":              round(acc * 100, 2),
        "cv_mean":               round(cv_mean * 100, 2),
        "cv_std":                round(cv_std * 100, 2),
        "confusion_matrix":      cm,
        "feature_importance":    importances,
        "classification_report": report,
        "n_samples":             len(X),
        "n_popular":             int(sum(y_np)),
        "n_not_popular":         int(len(y_np) - sum(y_np)),
        "trained":               True,
    }
    return _last_metrics

def predict_one(avg_stars, total_reviews, avg_price, price_std, competitor_count):
    global _model
    if not SKLEARN_OK:
        return {"error": "scikit-learn non installé"}
    if _model is None:
        result = train()
        if "error" in result:
            return result

    import numpy as np
    feat = np.array([[avg_stars, total_reviews, avg_price, price_std, competitor_count]], dtype=float)
    pred = int(_model.predict(feat)[0])
    proba = _model.predict_proba(feat)[0]
    classes = list(_model.classes_)

    idx_pop = classes.index(1) if 1 in classes else -1
    proba_pop = round(float(proba[idx_pop]) * 100, 2) if idx_pop >= 0 else 0.0
    proba_not = round(100 - proba_pop, 2)

    return {
        "prediction":      "Populaire" if pred == 1 else "Non-populaire",
        "is_popular":      pred == 1,
        "confidence":      round(float(max(proba)) * 100, 2),
        "proba_popular":   proba_pop,
        "proba_not_popular": proba_not,
    }

def get_all_predictions():
    global _model
    if not SKLEARN_OK:
        return []
    if _model is None:
        r = train()
        if "error" in r:
            return []

    import numpy as np
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.id, p.name, p.brand, p.category,
               COALESCE(AVG(r.stars), 0)        as avg_stars,
               COALESCE(SUM(r.review_count), 0)  as total_reviews,
               COALESCE(AVG(pr.price), 0)        as avg_price,
               COUNT(DISTINCT pr.competitor)      as competitor_count
        FROM products p
        LEFT JOIN reviews r  ON p.id = r.product_id
        LEFT JOIN prices pr  ON p.id = pr.product_id
        GROUP BY p.id
    """).fetchall()
    conn.close()

    results = []
    for row in rows:
        p = predict_one(row["avg_stars"], row["total_reviews"], row["avg_price"], 0, row["competitor_count"])
        actual_label = 1 if (row["avg_stars"] >= POPULAR_STARS and row["total_reviews"] >= POPULAR_REVIEWS) else 0
        results.append({
            "id":           row["id"],
            "name":         row["name"],
            "brand":        row["brand"],
            "category":     row["category"],
            "avg_stars":    round(row["avg_stars"], 2),
            "total_reviews":int(row["total_reviews"]),
            "avg_price":    round(row["avg_price"], 2),
            "prediction":   p.get("prediction", "N/A"),
            "is_popular":   p.get("is_popular", False),
            "confidence":   p.get("confidence", 0),
            "actual_label": "Populaire" if actual_label == 1 else "Non-populaire",
        })
    return results

def get_metrics():
    return _last_metrics

def is_trained():
    return _model is not None
