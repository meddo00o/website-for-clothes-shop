from __future__ import annotations

import json
import logging
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import t

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "store.db"
TELEGRAM_TOKEN=t.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=t.TELEGRAM_CHAT_ID
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "name": "Linen Tailored Shirt",
        "category": "Shirts",
        "badge": "New",
        "price": 820,
        "note": "Breathable structure with a relaxed luxury finish for daily wear.",
        "sizes": ["S", "M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #f6ebde, #c9af95)",
    },
    {
        "id": 2,
        "name": "Minimal Overshirt",
        "category": "Outerwear",
        "badge": "Best Seller",
        "price": 1150,
        "note": "A clean transitional layer designed for polished casual styling.",
        "sizes": ["M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #5b473d, #2d2521)",
    },
    {
        "id": 3,
        "name": "Straight-Leg Denim",
        "category": "Bottoms",
        "badge": "Editor Pick",
        "price": 980,
        "note": "Balanced volume and a softer wash to anchor the full wardrobe.",
        "sizes": ["30", "32", "34", "36"],
        "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #a6b3ca, #5a677f)",
    },
    {
        "id": 4,
        "name": "Merino Knit Polo",
        "category": "Knitwear",
        "badge": "Limited",
        "price": 760,
        "note": "Refined texture and a compact collar for smarter day-to-night styling.",
        "sizes": ["S", "M", "L"],
        "image": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #e6ddcf, #9f8b77)",
    },
    {
        "id": 5,
        "name": "Cropped Utility Jacket",
        "category": "Outerwear",
        "badge": "New",
        "price": 1420,
        "note": "Sharper seams and practical pockets without losing a clean silhouette.",
        "sizes": ["M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1495385794356-15371f348c31?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #baa78f, #6f5647)",
    },
    {
        "id": 6,
        "name": "Wide Pleat Trousers",
        "category": "Bottoms",
        "badge": "Essential",
        "price": 890,
        "note": "High-rise tailoring that gives simple outfits stronger presence.",
        "sizes": ["30", "32", "34", "36"],
        "image": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=900&q=80",
        "swatch": "linear-gradient(145deg, #dfd8d1, #8d847d)",
    },
]

DEFAULT_REVIEWS = [
    {
        "name": "Omar Hassan",
        "role": "Returning customer",
        "rating": 5,
        "comment": "The site finally looks like the pricing makes sense. It feels premium before checkout.",
    },
    {
        "name": "Salma Nabil",
        "role": "First-time buyer",
        "rating": 5,
        "comment": "The product presentation is clear, and the size information gives confidence quickly.",
    },
    {
        "name": "Youssef Adel",
        "role": "Creative director",
        "rating": 4,
        "comment": "This feels closer to a real brand launch page now, not just a static template.",
    },
]

SUPPORT_INFO = {
    "phone": "+20 100 123 4567",
    "email": "support@abdostore.com",
    "hours": "Daily from 10:00 AM to 10:00 PM",
}


def is_admin_authenticated() -> bool:
    return session.get("is_admin") is True


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def serialize_product(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "badge": row["badge"],
        "price": row["price"],
        "note": row["note"],
        "sizes": json.loads(row["sizes"]),
        "image": row["image"],
        "swatch": row["swatch"],
    }


def serialize_review(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"],
        "rating": row["rating"],
        "comment": row["comment"],
        "created_at": row["created_at"],
    }


def init_db() -> None:
    connection = get_db_connection()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            badge TEXT NOT NULL,
            price INTEGER NOT NULL,
            note TEXT NOT NULL,
            sizes TEXT NOT NULL,
            image TEXT NOT NULL,
            swatch TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            size TEXT NOT NULL,
            price INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """
    )

    product_count = connection.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
    if product_count == 0:
        connection.executemany(
            """
            INSERT INTO products (id, name, category, badge, price, note, sizes, image, swatch)
            VALUES (:id, :name, :category, :badge, :price, :note, :sizes, :image, :swatch)
            """,
            [{**product, "sizes": json.dumps(product["sizes"])} for product in DEFAULT_PRODUCTS],
        )

    review_count = connection.execute("SELECT COUNT(*) AS count FROM reviews").fetchone()["count"]
    if review_count == 0:
        now = datetime.utcnow().isoformat(timespec="seconds")
        connection.executemany(
            """
            INSERT INTO reviews (name, role, rating, comment, created_at)
            VALUES (:name, :role, :rating, :comment, :created_at)
            """,
            [{**review, "created_at": now} for review in DEFAULT_REVIEWS],
        )

    connection.commit()
    connection.close()


def fetch_products() -> list[dict]:
    connection = get_db_connection()
    rows = connection.execute(
        """
        SELECT id, name, category, badge, price, note, sizes, image, swatch
        FROM products
        ORDER BY id ASC
        """
    ).fetchall()
    connection.close()
    return [serialize_product(row) for row in rows]


def fetch_reviews() -> list[dict]:
    connection = get_db_connection()
    rows = connection.execute(
        """
        SELECT id, name, role, rating, comment, created_at
        FROM reviews
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()
    return [serialize_review(row) for row in rows]


def reviews_summary(reviews: list[dict]) -> dict:
    count_reviews = len(reviews)
    average = round(sum(review["rating"] for review in reviews) / count_reviews, 1) if count_reviews else 0
    return {"count": count_reviews, "average": average}


def send_telegram_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Telegram notification failed: %s", exc)


def parse_sizes(raw_sizes: str) -> list[str]:
    sizes = [size.strip() for size in raw_sizes.split(",") if size.strip()]
    return sizes


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/admin")
def admin():
    if not is_admin_authenticated():
        return render_template("admin.html", authenticated=False)

    return render_template("admin.html", authenticated=True, products=fetch_products())


@app.post("/admin/login")
def admin_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin"))

    return render_template("admin.html", authenticated=False, login_error="Invalid admin credentials.")


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin"))


@app.post("/admin/products")
def admin_create_product():
    if not is_admin_authenticated():
        return redirect(url_for("admin"))

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    badge = request.form.get("badge", "").strip()
    note = request.form.get("note", "").strip()
    image = request.form.get("image", "").strip()
    swatch = request.form.get("swatch", "").strip()
    sizes = parse_sizes(request.form.get("sizes", ""))

    try:
        price = int(request.form.get("price", "0").strip())
    except ValueError:
        price = 0

    if not all([name, category, badge, note, image, swatch]) or price <= 0 or not sizes:
        return redirect(url_for("admin"))

    connection = get_db_connection()
    connection.execute(
        """
        INSERT INTO products (name, category, badge, price, note, sizes, image, swatch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, category, badge, price, note, json.dumps(sizes), image, swatch),
    )
    connection.commit()
    connection.close()
    return redirect(url_for("admin"))


@app.post("/admin/products/<int:product_id>/update")
def admin_update_product(product_id: int):
    if not is_admin_authenticated():
        return redirect(url_for("admin"))

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    badge = request.form.get("badge", "").strip()
    note = request.form.get("note", "").strip()
    image = request.form.get("image", "").strip()
    swatch = request.form.get("swatch", "").strip()
    sizes = parse_sizes(request.form.get("sizes", ""))

    try:
        price = int(request.form.get("price", "0").strip())
    except ValueError:
        price = 0

    if not all([name, category, badge, note, image, swatch]) or price <= 0 or not sizes:
        return redirect(url_for("admin"))

    connection = get_db_connection()
    connection.execute(
        """
        UPDATE products
        SET name = ?, category = ?, badge = ?, price = ?, note = ?, sizes = ?, image = ?, swatch = ?
        WHERE id = ?
        """,
        (name, category, badge, price, note, json.dumps(sizes), image, swatch, product_id),
    )
    connection.commit()
    connection.close()
    return redirect(url_for("admin"))


@app.post("/admin/products/<int:product_id>/delete")
def admin_delete_product(product_id: int):
    if not is_admin_authenticated():
        return redirect(url_for("admin"))

    connection = get_db_connection()
    connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
    connection.commit()
    connection.close()
    return redirect(url_for("admin"))


@app.get("/health")
def healthcheck():
    return jsonify({"status": "ok"}), 200


@app.get("/api/products")
def get_products():
    return jsonify({"products": fetch_products()})


@app.get("/api/support")
def get_support():
    return jsonify(SUPPORT_INFO)


@app.get("/api/reviews")
def get_reviews():
    reviews = fetch_reviews()
    return jsonify({"reviews": reviews, "summary": reviews_summary(reviews)})


@app.post("/api/reviews")
def create_review():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    role = str(payload.get("role", "")).strip()
    comment = str(payload.get("comment", "")).strip()

    try:
        rating = int(payload.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0

    if len(name) < 2:
        return jsonify({"error": "Enter your name."}), 400
    if len(role) < 2:
        return jsonify({"error": "Enter your role or purchase context."}), 400
    if rating < 1 or rating > 5:
        return jsonify({"error": "Choose a rating from 1 to 5."}), 400
    if len(comment) < 12:
        return jsonify({"error": "Write a more complete review."}), 400

    now = datetime.utcnow().isoformat(timespec="seconds")
    connection = get_db_connection()
    cursor = connection.execute(
        """
        INSERT INTO reviews (name, role, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, role, rating, comment, now),
    )
    connection.commit()
    row = connection.execute(
        """
        SELECT id, name, role, rating, comment, created_at
        FROM reviews
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    connection.close()

    send_telegram_message(
        "\n".join(
            [
                f"⭐ <b>New Review #{row['id']}</b>",
                "",
                f"👤 Name: {row['name']}",
                f"🧾 Role: {row['role']}",
                f"🌟 Rating: {row['rating']}/5",
                "",
                "💬 Comment:",
                row["comment"],
            ]
        )
    )

    reviews = fetch_reviews()
    return jsonify(
        {
            "message": "Review submitted successfully.",
            "review": serialize_review(row),
            "summary": reviews_summary(reviews),
        }
    ), 201


@app.post("/api/newsletter")
def newsletter():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()

    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required."}), 400

    now = datetime.utcnow().isoformat(timespec="seconds")
    connection = get_db_connection()
    try:
        connection.execute(
            "INSERT INTO newsletter_subscribers (email, created_at) VALUES (?, ?)",
            (email, now),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        connection.close()
        return jsonify({"message": f"{email} is already subscribed."}), 200
    connection.close()

    send_telegram_message(f"📩 <b>New Newsletter Signup</b>\n\nEmail: {email}")
    return jsonify({"message": f"{email} subscribed successfully."}), 201


@app.post("/api/checkout")
def checkout():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    address = str(payload.get("address", "")).strip()
    payment_method = str(payload.get("payment_method", "")).strip()
    cart_items = payload.get("cart", [])

    if not all([name, phone, address, payment_method]) or not isinstance(cart_items, list) or not cart_items:
        return jsonify({"error": "Complete all checkout fields first."}), 400

    product_map = {product["id"]: product for product in fetch_products()}
    resolved_items = []
    total = 0

    for item in cart_items:
        product = product_map.get(item.get("id"))
        if not product:
            return jsonify({"error": "Invalid product."}), 400

        size = str(item.get("size", "")).strip()
        if size not in product["sizes"]:
            return jsonify({"error": f"Choose a valid size for {product['name']}."}), 400

        resolved_item = {
            "product_id": product["id"],
            "product_name": product["name"],
            "size": size,
            "price": product["price"],
        }
        resolved_items.append(resolved_item)
        total += product["price"]

    now = datetime.utcnow().isoformat(timespec="seconds")
    connection = get_db_connection()
    cursor = connection.execute(
        """
        INSERT INTO orders (customer_name, phone, address, payment_method, total, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, phone, address, payment_method, total, now),
    )
    order_id = cursor.lastrowid
    connection.executemany(
        """
        INSERT INTO order_items (order_id, product_id, product_name, size, price)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (order_id, item["product_id"], item["product_name"], item["size"], item["price"])
            for item in resolved_items
        ],
    )
    connection.commit()
    connection.close()

    lines = [
        f"🛒 <b>New Order #{order_id}</b>",
        "",
        f"👤 Name: {name}",
        f"📱 Phone: {phone}",
        f"🏠 Address: {address}",
        f"💳 Payment: {payment_method}",
        "",
        f"💰 Total: {total}",
        "",
        "📦 Items:",
    ]
    lines.extend([f"- {item['product_name']} ({item['size']}) - {item['price']}" for item in resolved_items])
    send_telegram_message("\n".join(lines))

    return jsonify({"message": f"Order #{order_id} placed successfully.", "order_id": order_id, "total": total}), 201


init_db()


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled server error: %s", error)
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
