"""Flask application for the Desi Pizza website."""
from pathlib import Path

from flask import (
    Flask, abort, redirect, render_template,
    request, session, url_for,
)
import json
# Get the folder location where this Python file is saved.
BASE_DIR = Path(__file__).resolve().parent

# Create the Flask application and set the template and static folders.
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "Templates")
)

# Set the secret key used to protect Flask session data.
app.secret_key = "desi-pizza-secret-key"


def load_pizzas():
    """Load pizza information from the JSON file."""
    # Open the pizza data file and read its JSON information.
    with (BASE_DIR / "data" / "pizza.json").open(
        "r", encoding="utf-8"
    ) as file:
        return json.load(file)


def save_order(order):
    """Save a completed order to the orders JSON file."""
    # Find the file used to store completed orders.
    file_path = BASE_DIR / "data" / "orders.json"

    # Read the existing orders from the JSON file.
    with file_path.open("r", encoding="utf-8") as file:
        orders = json.load(file)

    # Add the new completed order to the list.
        orders.append(order)

    # Save the updated list back to the JSON file.
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(orders, file, indent=4)


@app.route("/")
def index():
    """Display the homepage with pizza information."""
    # Load pizza information for the homepage.
    pizzas = load_pizzas()

    # Display the homepage and pass the pizza data to its template.
    return render_template("index.html", pizzas=pizzas)


@app.route("/about")
def about():
    """Display the restaurant's about page."""
    # Display information about the restaurant.
    return render_template("about.html")


@app.route("/menu")
def menu():
    """Display the menu page with pizza information."""
    # Load the available pizzas and their details.
    pizzas = load_pizzas()

    # Display the menu using the pizza information.
    return render_template('menu.html', pizzas=pizzas)


@app.route("/order-history")
def order_history():
    """Display the current session's orders and prices."""
    # Get the current orders, or an empty list if there are none.
    orders = session.get("orders", [])

    # Load pizza data to look up any missing prices.
    pizzas = load_pizzas()

    # Check each order to see whether its price is missing.
    for order in orders:
        if "price" not in order:
            pizza = order.get("pizza")
            size = order.get("size")

        # Find the correct price using the pizza name and size.
            if pizza in pizzas and size in pizzas[pizza]["prices"]:
                order["price"] = pizzas[pizza]["prices"][size]

    # Save the updated orders back into the session.
    session["orders"] = orders
    session.modified = True

    # Display the order history page with the current orders.
    return render_template("order_history.html", orders=orders)


@app.route("/order", methods=["POST"])
def order():
    """Add a valid pizza, drink, or snack to the session."""
    # Get the selected item and size from the submitted form.
    pizza = request.form.get("pizza", "").strip()
    size = request.form.get("size", "").strip()

    # Load pizza information to check the selected pizza.
    pizzas = load_pizzas()

    # Check whether the selected item is a pizza.

    # Pizza orders
    if pizza in pizzas:
        # Reject a size that is not available for this pizza.
        if size not in pizzas[pizza]["prices"]:
            abort(400, description="Please choose a valid pizza size.")
        price = pizzas[pizza]["prices"][size]

    # If it is not a pizza, check whether it is a drink or snack.
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

    # Create an empty order list if the session has none.
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
    """Remove an order from the session using its index."""
    # Get the current orders from the session.
    orders = session.get("orders", [])

    if 0 <= index < len(orders):
        orders.pop(index)

    session["orders"] = orders
    session.modified = True

    return redirect(url_for("order_history", removed=1))


@app.route("/checkout", methods=["POST"])
def checkout():
    """Validate checkout details and display the receipt."""
    # Get the current orders from the session.
    orders = session.get("orders", [])

    if not orders:
        return redirect(url_for("order_history"))

    # Get the customer's details from the checkout form.
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    payment = request.form.get("payment", "").strip()

    # Check that required details are provided and payment is valid.
    if not all((name, phone, address)) or payment not in {"Cash", "Card"}:
        abort(400, description="Please complete all checkout fields.")

    # Calculate the total price of all items in the order.
    total = sum(float(order.get("price", 0)) for order in orders)

    # Display the receipt with the order and customer information.
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
    """Save the completed order and clear the session orders."""
    # Get the current orders from the session.
    orders = session.get("orders", [])

    if not orders:
        return redirect(url_for("order_history"))

    # Get the customer's details from the checkout form.
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
    """Display the pizza gallery."""
    # Show the gallery page.
    return render_template("gallery.html")


@app.route("/hot-deals")
def hot_deals():
    """Display the restaurant's current deals."""
    # Show the hot deals page.
    return render_template("hot_deals.html")

# Start the Flask development server when this file runs directly.


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
