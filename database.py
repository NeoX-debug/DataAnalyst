import sqlite3

DB_PATH = "data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            competitor TEXT NOT NULL,
            price REAL NOT NULL,
            date_collected DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            stars REAL NOT NULL CHECK(stars >= 1 AND stars <= 5),
            review_count INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            spec_key TEXT NOT NULL,
            spec_value TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_db()
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
        conn.close()
        return

    products = [
        ("iPhone 15 Pro", "Smartphone", "Apple",
         [("Amazon",1199.99),("Fnac",1219.00),("Cdiscount",1149.99),("Darty",1229.99),("Boulanger",1209.00)],
         [(4.7,1423,"Amazon"),(4.5,892,"Fnac"),(4.6,532,"Cdiscount")],
         [("Processeur","A17 Pro"),("RAM","8 Go"),("Stockage","256 Go"),("Écran",'6.1" OLED'),("OS","iOS 17")]),

        ("Samsung Galaxy S24 Ultra", "Smartphone", "Samsung",
         [("Amazon",1299.00),("Fnac",1319.99),("Cdiscount",1249.00),("Darty",1309.00),("Boulanger",1289.99)],
         [(4.4,987,"Amazon"),(4.3,654,"Fnac"),(4.5,345,"Cdiscount")],
         [("Processeur","Snapdragon 8 Gen 3"),("RAM","12 Go"),("Stockage","256 Go"),("OS","Android 14")]),

        ("MacBook Air M2", "Laptop", "Apple",
         [("Amazon",1299.00),("Fnac",1319.00),("Cdiscount",1269.00),("Darty",1349.00),("Boulanger",1309.00)],
         [(4.8,2134,"Amazon"),(4.7,1456,"Fnac"),(4.9,876,"Cdiscount")],
         [("Processeur","Apple M2"),("RAM","8 Go"),("SSD","256 Go"),("Écran",'13.6" Liquid Retina'),("OS","macOS Ventura")]),

        ("Dell XPS 13", "Laptop", "Dell",
         [("Amazon",1199.00),("Fnac",1229.00),("Cdiscount",1149.00),("Darty",1219.00),("Boulanger",1199.00)],
         [(4.1,456,"Amazon"),(3.9,234,"Fnac"),(4.0,178,"Cdiscount")],
         [("Processeur","Intel Core i7-1260P"),("RAM","16 Go"),("SSD","512 Go"),("OS","Windows 11")]),

        ("Sony WH-1000XM5", "Casque Audio", "Sony",
         [("Amazon",329.99),("Fnac",349.00),("Cdiscount",299.99),("Darty",339.00),("Boulanger",319.00)],
         [(4.8,4231,"Amazon"),(4.7,2156,"Fnac"),(4.8,1432,"Cdiscount")],
         [("Type","Circum-aural"),("ANC","Oui"),("Autonomie","30h"),("Connexion","Bluetooth 5.2")]),

        ("Bose QuietComfort 45", "Casque Audio", "Bose",
         [("Amazon",279.99),("Fnac",299.00),("Cdiscount",259.99),("Darty",289.00),("Boulanger",274.00)],
         [(4.5,2156,"Amazon"),(4.4,1234,"Fnac"),(4.6,876,"Cdiscount")],
         [("Type","Circum-aural"),("ANC","Oui"),("Autonomie","24h"),("Connexion","Bluetooth 5.1")]),

        ("Samsung QLED 55\"", "TV", "Samsung",
         [("Amazon",799.99),("Fnac",849.00),("Cdiscount",749.99),("Darty",829.00),("Boulanger",809.00)],
         [(4.3,1456,"Amazon"),(4.2,987,"Fnac"),(4.1,654,"Cdiscount")],
         [("Taille",'55"'),("Résolution","4K"),("Technologie","QLED"),("HDR","HDR10+"),("Smart TV","Oui")]),

        ("LG OLED 55\" C3", "TV", "LG",
         [("Amazon",1199.99),("Fnac",1249.00),("Cdiscount",1149.99),("Darty",1229.00),("Boulanger",1199.00)],
         [(4.6,1893,"Amazon"),(4.7,1234,"Fnac"),(4.5,876,"Cdiscount")],
         [("Taille",'55"'),("Résolution","4K"),("Technologie","OLED"),("HDR","Dolby Vision"),("Smart TV","webOS 23")]),

        ("iPad Air 5", "Tablette", "Apple",
         [("Amazon",749.00),("Fnac",769.00),("Cdiscount",719.00),("Darty",759.00),("Boulanger",749.00)],
         [(4.5,2341,"Amazon"),(4.6,1567,"Fnac"),(4.4,987,"Cdiscount")],
         [("Processeur","Apple M1"),("RAM","8 Go"),("Stockage","64 Go"),("Écran",'10.9" Liquid Retina'),("OS","iPadOS 16")]),

        ("Xiaomi 13 Pro", "Smartphone", "Xiaomi",
         [("Amazon",899.99),("Fnac",929.00),("Cdiscount",869.99),("Darty",909.00),("Boulanger",899.00)],
         [(4.2,987,"Amazon"),(4.1,654,"Fnac"),(4.3,432,"Cdiscount")],
         [("Processeur","Snapdragon 8 Gen 2"),("RAM","12 Go"),("Stockage","256 Go"),("OS","MIUI 14")]),

        ("HP Spectre x360", "Laptop", "HP",
         [("Amazon",1499.00),("Fnac",1549.00),("Cdiscount",1449.00),("Darty",1529.00),("Boulanger",1499.00)],
         [(3.8,234,"Amazon"),(3.7,145,"Fnac"),(3.9,98,"Cdiscount")],
         [("Processeur","Intel Core i7-1255U"),("RAM","16 Go"),("SSD","512 Go"),("OS","Windows 11")]),

        ("JBL Charge 5", "Enceinte", "JBL",
         [("Amazon",179.99),("Fnac",189.00),("Cdiscount",169.99),("Darty",184.00),("Boulanger",179.00)],
         [(4.7,5621,"Amazon"),(4.6,3421,"Fnac"),(4.8,2134,"Cdiscount")],
         [("Type","Portable"),("Autonomie","20h"),("Résistance","IP67"),("Connexion","Bluetooth 5.1")]),
    ]

    for name, cat, brand, prices, revs, specs in products:
        c.execute("INSERT INTO products (name, category, brand) VALUES (?,?,?)", (name, cat, brand))
        pid = c.lastrowid
        for comp, price in prices:
            c.execute("INSERT INTO prices (product_id, competitor, price) VALUES (?,?,?)", (pid, comp, price))
        for stars, count, source in revs:
            c.execute("INSERT INTO reviews (product_id, stars, review_count, source) VALUES (?,?,?,?)", (pid, stars, count, source))
        for key, val in specs:
            c.execute("INSERT INTO specs (product_id, spec_key, spec_value) VALUES (?,?,?)", (pid, key, val))

    conn.commit()
    conn.close()
