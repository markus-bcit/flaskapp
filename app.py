from pathlib import Path
import datetime
from flask import Flask, jsonify, render_template, request

from database import db
from models import Product
from models import Order
from models import ProductsOrder

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.instance_path = Path(".").resolve()
db.init_app(app)


@app.route("/")
def home() -> str:
    """
    Renders the home page of the web application with all the products available in the store.

    Returns:
        str: A HTML string that displays all the products available in the store.
    """
    data = Product.query.all()
    return render_template("index.html", products=data)

@app.route("/api/product/<string:name>", methods=["GET"])
def api_get_product(name) -> dict:
    """
    Retrieves a product from the database by its name.

    Args:
        name (str): The name of the product to retrieve.
    Returns:
        json: A JSON object that represents the retrieved product in a dict or an error message.
    """
    product = db.session.get(Product, name.lower())
    if product is None:
        return f"Item not found in the database", 404
    product_json = product.to_dict()
    return jsonify(product_json)


@app.route("/api/product", methods=["POST"])
def api_create_product():
    """
    Creates a new product in the database based on the JSON data provided in the request.

    Returns:
        str: A message indicating whether the product was added to the database or 
             an error message if the provided JSON data is invalid.
    """
    data = request.json
    # Check all data is provided
    for key in ("name", "price", "quantity"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400

    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        # Make sure they are positive
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )

    product = Product(
        name=data["name"],
        price=price,
        quantity=quantity,
    )
    db.session.add(product)
    db.session.commit()
    return "Item added to the database"


@app.route("/api/product/<string:name>", methods=["DELETE"])
def api_delete_product(name):
    """
    Deletes a product from the database by its name.

    Args:
        name (str): The name of the product to delete.

    Returns:
        str: A message indicating whether the product was deleted from the database.
    """
    product = db.session.get(Product, name.lower())
    db.session.delete(product)
    db.session.commit()
    return 'Product deleted from the database'


@app.route("/api/product/<string:name>", methods=["PUT"])
def api_update_product(name):
    """
    Updates a product in the database by its name based on the JSON data provided in the request.

    Args:
        name (str): The name of the product to update.

    Returns:
        str: A message indicating whether the product was updated or an error message if the provided JSON data is invalid.
    """
    data = request.json
    # Check all data is provided

    if 'price' not in data.keys() and 'quantity' not in data.keys():
        return f"The JSON provided is invalid", 400

    try:
        price = float(data["price"])
        quantity = int(data["quantity"])
        if price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        return (
            "Invalid values: price must be a positive float and quantity a positive integer",
            400,
        )
    product = db.session.get(Product, name.lower())
    product.price = price
    product.quantity = quantity
    db.session.commit()
    return 'Product updated'


@app.route("/api/order/<int:order_id>", methods=["GET"])
def api_get_order(order_id):
    """
    Retrieves an order from the database by its ID.

    Args:
        order_id (int): The ID of the order to retrieve.

    Returns:
        json: A JSON object that represents the retrieved order.
    """
    order = db.session.get(Order, order_id)
    order_json = order.to_dict(True)
    return jsonify(order_json)


@app.route("/api/order/<int:order_id>", methods=["PUT"])
def api_process_order(order_id):
    """
    Processes an order in the database by updating the quantity of products in stock.

    Args:
        order_id (int): The ID of the order to process.

    Returns:
        json: A JSON object that represents the processed order.
    """
    order = db.session.get(Order, order_id)
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M")

    for product_order in order.products:
        product_obj = db.session.get(Product, product_order.product_name)
        if (product_obj.quantity - product_order.quantity) < 0:
            product_order.quantity = product_obj.quantity
            product_obj.quantity = 0
        else:
            product_obj.quantity -= product_order.quantity

        db.session.add(product_obj)
        db.session.commit()
    order.date_processed = date
    order.completed = True
    db.session.add(order)

    db.session.commit()

    return api_get_order(order_id)


@app.route("/api/order", methods=["POST"])
def api_create_order():
    """
    Creates a new order in the database based on the JSON data provided in the request.

    Returns:
        json: A JSON object that represents the newly created order or an error message if the provided JSON data is invalid.
    """
    data = request.json
    # Check all data is provided

    for key in ("customer_name", "customer_address", "completed", "products", "date_created", "date_processed"):
        if key not in data:
            return f"The JSON provided is invalid (missing: {key})", 400
    for item in data["products"]:
        for key in item.keys():
            if key not in ("product_name", "quantity"):
                return f"The JSON provided is invalid, 'products' is missing a key", 400

    for product in data["products"]:
        if db.session.get(Product, product["product_name"]) is None:
            return f"Item not found in the database", 400

    if not isinstance(data['completed'], bool):
        return f"The JSON completed provided is invalid", 400

    try:
        product_orders = []
        for product in data["products"]:
            if db.session.get(Product, product["product_name"]) is None:
                return f"Item not found in the database", 400
            else:
                quantity = int(product["quantity"])
            if quantity < 0:
                raise ValueError

            else:
                product_obj = ProductsOrder(
                    product_name=product["product_name"], quantity=quantity)
                product_orders.append(product_obj)
    except ValueError:
        return (
            "Invalid values: quantity must be a positive integer",
            400,
        )
    order = Order(
        name=data["customer_name"],
        address=data["customer_address"],
        completed=data["completed"],
        date_created=data["date_created"],
        date_processed=data["date_processed"],
        products=product_orders)
    db.session.add(order)
    db.session.commit()
    order_json = order.to_dict()
    return jsonify(order_json)

@app.route("/api/products", methods=["GET"])
def get_products() -> str:
    """
    Renders the home page of the web application with all the products available in the store.

    Returns:
        str: A HTML string that displays all the products available in the store.
    """
    product_lists = []
    data = Product.query.all()
    for product in data:
        product_lists.append(product.to_dict())
    return jsonify(product_lists)

@app.route("/api/orders", methods=["GET"])
def get_orders() -> str:
    """
    Renders the home page of the web application with all the products available in the store.

    Returns:
        str: A HTML string that displays all the products available in the store.
    """
    order_list = []
    data = Order.query.all()
    for order in data:
        order_list.append(order.to_dict(True))
    return jsonify(order_list)

@app.route("/api/order/<int:order_id>", methods=["DELETE"])
def api_delete_order(order_id):
    """
    Deletes a product from the database by its name.

    Args:
        name (str): The name of the product to delete.

    Returns:
        str: A message indicating whether the product was deleted from the database.
    """
    order = db.session.get(Order, order_id)
    db.session.delete(order)

    db.session.commit()
    return 'Order deleted from the database'

@app.route("/api/order/<int:order_id>", methods=["POST"])
def api_update_order(order_id):
    """
    Updates a product in the database by its name based on the JSON data provided in the request.

    Args:
        name (str): The name of the product to update.

    Returns:
        str: A message indicating whether the product was updated or an error message if the provided JSON data is invalid.
    """
    data = request.json
    # Check all data is provided

    for item in data:
        for key in item.keys():
            if key not in ("product_name", "quantity"):
                return f"The JSON provided is invalid, 'products' is missing a key", 400

    for product in data:
        if db.session.get(Product, product["product_name"]) is None:
            return f"Item not found in the database", 400

    try:
        product_orders = []
        for product in data:
            if db.session.get(Product, product["product_name"]) is None:
                return f"Item not found in the database", 400
            else:
                quantity = int(product["quantity"])
            if quantity < 0:
                raise ValueError
            product_obj = ProductsOrder(
                product_name=product["product_name"], quantity=quantity)
            product_orders.append(product_obj)
    except ValueError:
        return (
            "Invalid values: quantity must be a positive integer",
            400,
        )
    for item in data:
        product_order = db.session.query(ProductsOrder).get((item['product_name'], order_id ))
        db.session.delete(product_order)
    order = db.session.get(Order, order_id)
    order.products = product_orders
    db.session.commit()
    return "Order Updated successfully"

if __name__ == "__main__":
    app.run(debug=True)
