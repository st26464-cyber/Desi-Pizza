from pathlib import Path

from flask import Flask, render_template, render_template_string, request
from jinja2 import TemplateSyntaxError
import json

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "Templates")
)


def load_pizzas():
    with (BASE_DIR / "data" / "pizza.json").open("r", encoding="utf-8") as file:
        return json.load(file)

@app.route("/")
def index():
    pizzas = load_pizzas()
    try:
        return render_template("index.html", pizzas=pizzas)
    except TemplateSyntaxError:
        # Fallback for an index template that is missing a closing endblock.
        return render_template_string(
            """
            <!doctype html>
            <html lang="en">
                <head><meta charset="utf-8"><title>Desi Pizza</title></head>
                <body>
                    <h1>Desi Pizza</h1>
                    <p><a href="{{ url_for('menu') }}">View Menu</a></p>
                    <main>
                        {% for pizza in pizzas %}
                            <article>
                                <h2>{{ pizza.name }}</h2>
                                <ul>
                                    {% for size, details in pizza.sizes.items() %}
                                        <li>{{ size }}: ${{ details.price }} ({{ details.stock }} in stock)</li>
                                    {% endfor %}
                                </ul>
                            </article>
                        {% endfor %}
                    </main>
                </body>
            </html>
            """,
            pizzas=pizzas,
        )

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/menu")
def menu():
    pizzas = load_pizzas()
    return render_template('menu.html', pizzas=pizzas)

@app.route("/order", methods=["POST"])
def order():
   pizza = request.form.get("pizza")
   size = request.form.get("size")

   return f"You ordered a {size} {pizza}!"

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/hot-deals")
def hot_deals():
    return render_template("hot_deals.html")

if __name__ == "__main__":
    app.run(debug=True)
