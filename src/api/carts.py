from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    
    with db.engine.begin() as connection:
        new_customer_id = connection.execute(sqlalchemy.text("INSERT INTO custumers (name) VALUES ('" + str(new_cart.customer) + "') RETURNING id")).first()[0]
        new_cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (" + str(new_customer_id) + ") RETURNING id")).first()[0]

    return {"cart_id": new_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    i = item_sku[7:].split("_")
    print(i)
    r, g, b, t = i[0], i[1], i[2], i[3]


    with db.engine.begin() as connection:
        price = connection.execute(sqlalchemy.text("SELECT price FROM catalog WHERE name = '" + item_sku + "'")).first()[0]
        print(price)
        cur_price = connection.execute(sqlalchemy.text("SELECT price FROM carts WHERE id = " + str(cart_id))).first()[0]

        fin_price = cur_price + price * cart_item.quantity

        connection.execute(sqlalchemy.text("UPDATE carts SET price = " + str(fin_price) + " WHERE id = " + str(cart_id)))
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, r, g, b, t, sku, quantity) VALUES ("+str(cart_id)+", "+r+", "+g+", "+b+", "+t+", '"+item_sku+"', "+str(cart_item.quantity)+") RETURNING id")).first()[0]

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    with db.engine.begin() as connection:               # UPDATE GOLD BUT CHECKING THAT PAYMENT AND PRICE MATCH

        total_price = connection.execute(sqlalchemy.text("SELECT price FROM carts WHERE id = " + str(cart_id))).first()[0]

        #if total_price < int(cart_checkout.payment):   # MAKE SURE THEY PAY AT LEAST WHAT IT COSTS ;)
        #    return "Wrong amount of money paid"

        #cur_gold = connection.execute(sqlalchemy.text("SELECT * FROM gold")).first()[0]
        #fin_gold = cur_gold + total_price
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + " + str(total_price)))

        potions_bought = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = " + str(cart_id))).fetchall()

    total_potions_bought = 0
    for pot in potions_bought:
        print("Pot: " + str(pot))
        total_potions_bought += pot[7]

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = quantity - " + str(pot[7]) + " WHERE name = '" + pot[6] + "'"))
            connection.execute(sqlalchemy.text("DELETE FROM cart_items WHERE sku = '" + str(pot[6]) + "'"))
    
    with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = " + str(cart_id) + ""))
    
            
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_price}
