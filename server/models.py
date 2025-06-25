from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    resturant_pizzas = db.relationship('RestaurantPizza', back_populates='restaurant', cascade='all, delete-orphan')

    # add serialization rules
    serialize_rules = ('-restaurant_pizzas.restaurant',)
    
    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "address":self.address,
            
            # "restaurant_pizzas":{
            #     "id":self.id,
            #     "pizza":{
            #         "id":self.id,
            #         "ingredients":self.resturant_pizzas.ingredients,
            #         "name": self.pizza_name
            #     },
            #     "pizza_id": self.resturant_pizzas_pizza_id,
            #     "price":self.resturant_pizzas_price,
            #     "restaurant_id":self.resturant_pizzas_restaurant_id
            # }
        }

    def __repr__(self):
        return f"<Restaurant {self.name}>"
    


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    resturant_pizzas = db.relationship('RestaurantPizza', back_populates='pizza', cascade='all, delete-orphan')

    # add serialization rules
    serialize_rules = ('-restaurant_pizzas.pizza',)
    def to_dict(self):
        return {
            "id":self.id,
            "name":self.name,
            "ingredients":self.ingredients,
        }
    

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'))
    
    pizza = db.relationship('Pizza', back_populates='resturant_pizzas')
    restaurant = db.relationship('Restaurant', back_populates='resturant_pizzas')

    # add serialization rules
    serialize_rules = ('-restaurant.restaurant_pizzas' ,'-pizza.restaurant_pizzas',)

    # add validation
    @validates('price')
    def validate_price(self, key, price):
        if price in range(1,31):
            return price 
    
    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"
