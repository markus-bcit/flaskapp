from database import db


class Product(db.Model):
    """
    Represents a product with a name, price, and quantity.

    Attributes:
    - name (str): The name of the product (primary key).
    - price (float): The price of the product (must be non-null).
    - quantity (int): The quantity of the product (nullable).

    Methods:
    - to_dict(): Returns a dictionary representation of the object.
    - remove(): Removes the object from the database. 
    """
    name = db.Column(db.String, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        return {"name": self.name, "quantity": self.quantity, "price": self.price,}
    
    def remove(self):
        db.delete(self.name)

class Order(db.Model):
    """
    Represents an order with an ID, customer name and address, and a list of ProductsOrder.

    Attributes:
    - id (int): The ID of the order (primary key).
    - name (str): The name of the customer who placed the order.
    - address (str): The address of the customer who placed the order.
    - completed (bool): Whether the order has been completed.
    - products (list of ProductsOrder): The list of products included in the order.

    Methods:
    - to_dict(): Returns a dictionary representation of the object, including the list of products and the total price of the order.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)
    completed = db.Column(db.Boolean)
    date_created = db.Column(db.String)
    date_processed = db.Column(db.String)
    products = db.relationship('ProductsOrder', back_populates='order', cascade="all")
    
    def to_dict(self, id_bool=False) -> dict:
        """Forms a dict using the order and products

        Returns:
            dic (dict): dictionary containing the name, 
                        address, products, total price of order
        """
        dic = {}
        product_list = []
        price = 0
        for product in self.products:
            product_list.append(product.to_dict())
            
        for item in product_list:
            item.pop('order_id')

        for item in product_list:
            product = db.session.get(Product, item["product_name"])
            price += product.to_dict()['price'] * item["quantity"]
        if id_bool == True:
            dic["order_id"] = self.id
            dic["completed"] = self.completed
            
        dic["customer_name"] = self.name
        dic["customer_address"] = self.address
        dic["date_created"] = self.date_created
        dic["date_processed"] = self.date_processed
        dic["products"] = product_list
        dic["price"] = round(price, 2)
        return dic
    
class ProductsOrder(db.Model):
    """
    Represents the relationship between a product and an order, with a quantity.

    Attributes:
    - product_name (str): The name of the product (foreign key to Product.name).
    - order_id (int): The ID of the order (foreign key to Order.id).
    - quantity (int): The quantity of the product in the order (must be non-null).

    Relationships:
    - product: The Product object associated with the order.
    - order: The Order object associated with the product.

    Methods:
    - to_dict(): Returns a dictionary representation of the object.
    """
    # Product foreign key is name
    product_name = db.Column(db.ForeignKey("product.name"), primary_key=True)
    # Order foreign key is ID
    order_id = db.Column(db.ForeignKey("order.id"), primary_key=True)
    # This is how many items we want
    quantity = db.Column(db.Integer, nullable=False)
    # Relationships and backreferences for SQL Alchemy
    product = db.relationship('Product')
    order = db.relationship('Order', back_populates='products')
    def to_dict(self):
        return {"product_name": self.product_name, "order_id": self.order_id, "quantity": self.quantity}
