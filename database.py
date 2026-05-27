import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marketplace.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        password TEXT NOT NULL DEFAULT '123456'
    )
    ''')
    
    try:
        cursor.execute("SELECT password FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN password TEXT NOT NULL DEFAULT '123456'")
        conn.commit()
    
    # 2. Shops Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name TEXT NOT NULL,
        category TEXT UNIQUE NOT NULL,
        commission_pct REAL DEFAULT 5.0,
        username TEXT,
        password TEXT NOT NULL DEFAULT '123456',
        image_url TEXT
    )
    ''')
    
    try:
        cursor.execute("SELECT password FROM shops LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE shops ADD COLUMN username TEXT")
            cursor.execute("ALTER TABLE shops ADD COLUMN password TEXT NOT NULL DEFAULT '123456'")
            conn.commit()
        except Exception:
            pass

    try:
        cursor.execute("SELECT image_url FROM shops LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE shops ADD COLUMN image_url TEXT")
            conn.commit()
        except Exception:
            pass
    
    # 3. Products Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        is_available BOOLEAN DEFAULT 1,
        image_url TEXT,
        FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
    )
    ''')
    
    try:
        cursor.execute("SELECT image_url FROM products LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
            conn.commit()
        except Exception:
            pass

    # 4. Delivery Partners Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS delivery_partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        active_orders INTEGER DEFAULT 0,
        availability_status TEXT DEFAULT 'online',
        cooldown_until TIMESTAMP NULL,
        username TEXT,
        password TEXT NOT NULL DEFAULT '123456'
    )
    ''')
    
    try:
        cursor.execute("SELECT password FROM delivery_partners LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE delivery_partners ADD COLUMN username TEXT")
            cursor.execute("ALTER TABLE delivery_partners ADD COLUMN password TEXT NOT NULL DEFAULT '123456'")
            conn.commit()
        except Exception:
            pass
    
    # 5. Orders Table (State Machine Master)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        shop_id INTEGER NOT NULL,
        delivery_boy_id INTEGER,
        total_amount REAL NOT NULL,
        gst_amount REAL DEFAULT 0.0,
        priority_type TEXT DEFAULT 'NORMAL',
        status TEXT DEFAULT 'PENDING',
        pickup_otp TEXT,
        delivery_otp TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        assigned_at TIMESTAMP,
        accepted_at TIMESTAMP,
        ready_at TIMESTAMP,
        delivered_at TIMESTAMP,
        failure_reason TEXT,
        FOREIGN KEY (customer_id) REFERENCES users(id),
        FOREIGN KEY (shop_id) REFERENCES shops(id),
        FOREIGN KEY (delivery_boy_id) REFERENCES delivery_partners(id)
    )
    ''')
    
    # 6. Order Items Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')
    
    # 7. Admins Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully!")

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Seed Users
    users_data = [
        ('Alice Sharma', '9876543210', 'Flat 101, Sunshine Apartments, Sector 4', '123456'),
        ('Bob Verma', '8765432109', 'House 23, Green Valley Colony, Road 2', '123456'),
        ('Charlie Gupta', '7654321098', 'Penthouse B, Skyline Heights, Main Road', '123456')
    ]
    for user in users_data:
        try:
            cursor.execute('INSERT INTO users (name, phone, address, password) VALUES (?, ?, ?, ?)', user)
        except sqlite3.IntegrityError:
            pass # Already exists
            
    # Seed Shops
    shops_data = [
        ('Apna Bazaar (Kirana & General)', 'KIRANA', 5.0, 'kirana', '123456'),
        ('The Bakers Table (Premium Cakes)', 'CAKES', 8.0, 'cakes', '123456'),
        ('Fresh & Green Vegetables', 'VEGGIES', 4.0, 'veggies', '123456'),
        ('ElectroWorld Solutions', 'ELECTRONICS', 10.0, 'electronics', '123456')
    ]
    for shop in shops_data:
        try:
            cursor.execute('INSERT INTO shops (shop_name, category, commission_pct, username, password) VALUES (?, ?, ?, ?, ?)', shop)
        except sqlite3.IntegrityError:
            pass # Already exists
            
    # Update existing shops to populate username & password if they are empty
    cursor.execute("UPDATE shops SET username = 'kirana', password = '123456' WHERE category = 'KIRANA' AND username IS NULL")
    cursor.execute("UPDATE shops SET username = 'cakes', password = '123456' WHERE category = 'CAKES' AND username IS NULL")
    cursor.execute("UPDATE shops SET username = 'veggies', password = '123456' WHERE category = 'VEGGIES' AND username IS NULL")
    cursor.execute("UPDATE shops SET username = 'electronics', password = '123456' WHERE category = 'ELECTRONICS' AND username IS NULL")
            
    # Populate beautiful Unsplash category images for seeded shops if empty
    cursor.execute("UPDATE shops SET image_url = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&auto=format&fit=crop&q=60' WHERE category = 'KIRANA' AND image_url IS NULL")
    cursor.execute("UPDATE shops SET image_url = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60' WHERE category = 'CAKES' AND image_url IS NULL")
    cursor.execute("UPDATE shops SET image_url = 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&auto=format&fit=crop&q=60' WHERE category = 'VEGGIES' AND image_url IS NULL")
    cursor.execute("UPDATE shops SET image_url = 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=500&auto=format&fit=crop&q=60' WHERE category = 'ELECTRONICS' AND image_url IS NULL")

    conn.commit()
    
    # Fetch shop IDs for product mapping
    cursor.execute('SELECT id, category FROM shops')
    shop_ids = {row['category']: row['id'] for row in cursor.fetchall()}
    
    # Seed Products
    products_data = [
        # Kirana
        (shop_ids['KIRANA'], 'Milk 1L Packet', 50.0, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['KIRANA'], 'Bread Brown Slice', 40.0, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['KIRANA'], 'Amul Butter 100g', 60.0, 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['KIRANA'], 'Sugar 1kg Pack', 45.0, 'https://images.unsplash.com/photo-1581798459219-318e76aecc7b?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['KIRANA'], 'Tata Tea Premium 250g', 95.0, 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500&auto=format&fit=crop&q=60'),
        # Cakes
        (shop_ids['CAKES'], 'Chocolate Truffle Cake 500g', 450.0, 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['CAKES'], 'Red Velvet Cake 500g', 500.0, 'https://images.unsplash.com/photo-1616541823729-00fe0aacd32c?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['CAKES'], 'Sparkling Candles Pack', 35.0, 'https://images.unsplash.com/photo-1541417904950-b855846fe074?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['CAKES'], 'Birthday Cap Premium', 25.0, 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=500&auto=format&fit=crop&q=60'),
        # Veggies
        (shop_ids['VEGGIES'], 'Potato 1kg', 30.0, 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['VEGGIES'], 'Tomato 1kg', 40.0, 'https://images.unsplash.com/photo-1595855759920-86582396756a?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['VEGGIES'], 'Onion 1kg', 35.0, 'https://images.unsplash.com/photo-1508747703725-719ae257c84a?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['VEGGIES'], 'Fresh Coriander Bundle', 12.0, 'https://images.unsplash.com/photo-1608797178974-15b35a61d121?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['VEGGIES'], 'Fresh Lemon 250g', 25.0, 'https://images.unsplash.com/photo-1590502593747-42a996133562?w=500&auto=format&fit=crop&q=60'),
        # Electronics
        (shop_ids['ELECTRONICS'], 'Fast USB-C Cable 1.5m', 150.0, 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['ELECTRONICS'], 'Wired Earphones with Mic', 250.0, 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['ELECTRONICS'], 'AA Duracell Battery 4pc', 120.0, 'https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=500&auto=format&fit=crop&q=60'),
        (shop_ids['ELECTRONICS'], 'Smart WiFi Plug 16A', 599.0, 'https://images.unsplash.com/photo-1558002038-1055907df827?w=500&auto=format&fit=crop&q=60')
    ]
    
    for product in products_data:
        # Check if already seeded to avoid duplicates
        cursor.execute('SELECT id FROM products WHERE shop_id = ? AND name = ?', (product[0], product[1]))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO products (shop_id, name, price, image_url) VALUES (?, ?, ?, ?)', product)
        else:
            cursor.execute('UPDATE products SET image_url = ? WHERE shop_id = ? AND name = ? AND image_url IS NULL', (product[3], product[0], product[1]))
            
    # Seed Delivery Partners
    partners_data = [
        ('Rahul Rider', '9000000001', 0, 'online', 'rahul', '123456'),
        ('Amit Express', '9000000002', 0, 'online', 'amit', '123456'),
        ('Vicky Speedster', '9000000003', 0, 'offline', 'vicky', '123456')
    ]
    for partner in partners_data:
        try:
            cursor.execute('INSERT INTO delivery_partners (name, phone, active_orders, availability_status, username, password) VALUES (?, ?, ?, ?, ?, ?)', partner)
        except sqlite3.IntegrityError:
            pass
            
    # Update existing partners to populate username & password if they are empty
    cursor.execute("UPDATE delivery_partners SET username = 'rahul', password = '123456' WHERE phone = '9000000001' AND username IS NULL")
    cursor.execute("UPDATE delivery_partners SET username = 'amit', password = '123456' WHERE phone = '9000000002' AND username IS NULL")
    cursor.execute("UPDATE delivery_partners SET username = 'vicky', password = '123456' WHERE phone = '9000000003' AND username IS NULL")
    
    # Seed Admin accounts
    try:
        cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', 'admin123'))
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()
    print("Database seeded successfully with exclusive shops, products, users, and riders!")

if __name__ == '__main__':
    init_db()
    seed_db()
