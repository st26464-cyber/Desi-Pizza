from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for
import json

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "Templates")
)
app.secret_key = "desi-pizza-secret-key"

def load_pizzas():
    with (BASE_DIR / "data" / "pizza.json").open("r", encoding="utf-8") as file:
        return json.load(file)
def save_order(order):
    file_path = BASE_DIR / "data" / "orders.json"

    with file_path.open("r", encoding="utf-8") as file:
        orders = json.load(file)

    orders.append(order)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(orders, file, indent=4)

@app.route("/")
def index():
    pizzas = load_pizzas()
    return render_template("index.html", pizzas=pizzas)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/menu")
def menu():
    pizzas = load_pizzas()
    return render_template('menu.html', pizzas=pizzas)

@app.route("/order-history")
def order_history():
    orders = session.get("orders", [])
    pizzas = load_pizzas()

    for order in orders:
        if "price" not in order:
            pizza = order.get("pizza")
            size = order.get("size")

            if pizza in pizzas and size in pizzas[pizza]["prices"]:
                order["price"] = pizzas[pizza]["prices"][size]

    session["orders"] = orders
    session.modified = True

    return render_template("order_history.html", orders=orders)


@app.route("/order", methods=["POST"])
def order():
    pizza = request.form.get("pizza", "").strip()
    size = request.form.get("size", "").strip()

    pizzas = load_pizzas()

    # Pizza orders
    if pizza in pizzas:
        if size not in pizzas[pizza]["prices"]:
            abort(400, description="Please choose a valid pizza size.")
        price = pizzas[pizza]["prices"][size]

    # Drinks and snacks
    else:
        prices = {
            "Coke": 3.00,
            "Sprite": 3.00,
            "Pepsi": 3.00,
            "Mango Lassi": 5.00,
            "Monster Drink": 5.00,
            "L&P": 3.50,
            "Red Bull": 5.00,
            "Samosa": 4.00,
            "Paneer Pakora": 7.00,
            "Garlic Bread": 6.00,
            "Dipping Sauces": 2.00,
            "Cheesy Bites": 7.00,
            "French Fries": 5.00,
            "Waffle Fries": 6.00
        }

        if pizza not in prices:
            abort(404, description="Item not found.")

        price = prices[pizza]

    if "orders" not in session:
        session["orders"] = []

    session["orders"].append({
        "pizza": pizza,
        "size": size,
        "price": price
    })

    session.modified = True

    return redirect(url_for("menu", ordered=pizza))

@app.route("/remove-order/<int:index>", methods=["POST"])
def remove_order(index):
    orders = session.get("orders", [])

    if 0 <= index < len(orders):
        orders.pop(index)

    session["orders"] = orders
    session.modified = True

    return redirect(url_for("order_history", removed=1))

@app.route("/checkout", methods=["POST"])
def checkout():
    orders = session.get("orders", [])

    if not orders:
        return redirect(url_for("order_history"))

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    payment = request.form.get("payment", "").strip()
    if not all((name, phone, address)) or payment not in {"Cash", "Card"}:
        abort(400, description="Please complete all checkout fields.")

    total = sum(float(order.get("price", 0)) for order in orders)

    return render_template(
        "receipt.html",
        orders=orders,
        total=total,
        name=name,
        phone=phone,
        address=address,
        payment=payment,
    )
@app.route("/place-order", methods=["POST"])
def place_order():
    orders = session.get("orders", [])

    if not orders:
        return redirect(url_for("order_history"))

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    payment = request.form.get("payment", "").strip()

    if not all((name, phone, address)) or payment not in {"Cash", "Card"}:
        abort(400, description="Please complete all checkout fields.")

    total = sum(float(order.get("price", 0)) for order in orders)

    completed_order = {
        "name": name,
        "phone": phone,
        "address": address,
        "payment": payment,
        "orders": orders,
        "total": total
    }

    save_order(completed_order)

    session["orders"] = []
    session.modified = True

    return render_template(
        "receipt.html",
        orders=orders,
        total=total,
        name=name,
        phone=phone,
        address=address,
        payment=payment
    )
@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/hot-deals")
def hot_deals():
    return render_template("hot_deals.html")

if __name__ == "__main__":
     app.run(host="0.0.0.0", port=5000, debug=True)
