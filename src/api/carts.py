from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)





class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    with db.engine.begin() as connection:
        params = {
            'customer_name_filter': customer_name,
            'potion_sku_filter': potion_sku
        }

        query = """
    SELECT created_at AS timestamp, customer_name, item_sku, quantity * price AS line_item_total 
    FROM invoices
"""

        params = {}

        if customer_name and potion_sku:
            query += "WHERE customer_name LIKE :customer_name_filter AND item_sku LIKE :potion_sku_filter "
            params['customer_name_filter'] = f"%{customer_name}%"
            params['potion_sku_filter'] = f"%{potion_sku}%"
        elif customer_name:
            query += "WHERE customer_name LIKE :customer_name_filter "
            params['customer_name_filter'] = f"%{customer_name}%"
        elif potion_sku:
            query += "WHERE item_sku LIKE :potion_sku_filter "
            params['potion_sku_filter'] = f"%{potion_sku}%"

        order_by_clause = f"ORDER BY {sort_col.value} {sort_order.value.upper()}"
        query += order_by_clause

        if search_page == '':
            search_page = '0'

        result = connection.execute(sqlalchemy.text(query), params).fetchall()

        num = len(result)
        start = 5*int(search_page)
        end = 5*int(search_page)+5
        result = result[start:end]

    prev = str(int(search_page)-1)
    next = str(int(search_page)+1)

    print(result)

    search = {
        "previous": prev if int(prev) > -1 else '',
        "next": next if num < 6 else '',
        "results": [],
    }

    for i in range(len(result)):
        
        search['results'].append({
                "line_item_id": i,
                "item_sku": result[i][2],
                "customer_name": result[i][1],
                "line_item_total": result[i][3],
                "timestamp": result[i][0],
            })

    return search





class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    
    with db.engine.begin() as connection:
        customer = connection.execute(sqlalchemy.text("SELECT * FROM customers WHERE name = '" + str(new_cart.customer) + "'")).first()
        print(customer)
        if customer == None:
            new_customer_id = connection.execute(sqlalchemy.text("INSERT INTO customers (name) VALUES ('" + str(new_cart.customer) + "') RETURNING id")).first()[0]
        else:
            new_customer_id = customer[0]
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
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, r, g, b, t, sku, quantity, price) VALUES ("+str(cart_id)+", "+r+", "+g+", "+b+", "+t+", '"+item_sku+"', "+str(cart_item.quantity)+", " +str(price)+") RETURNING id")).first()[0]
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    with db.engine.begin() as connection:               # UPDATE GOLD 

        customer_id = connection.execute(sqlalchemy.text("SELECT customer_id  FROM carts WHERE id = " + str(cart_id))).first()[0]
        total_price = connection.execute(sqlalchemy.text("SELECT SUM(price * quantity)  FROM cart_items WHERE cart_id = " + str(cart_id))).first()[0]

        customer_name = connection.execute(sqlalchemy.text("SELECT name FROM customers WHERE id = " + str(customer_id))).first()[0]
        connection.execute(sqlalchemy.text("INSERT INTO gold (quantity, description) VALUES (" + str(total_price) + ", 'Cart checkout customer_id = "+str(customer_id)+"')"))

        potions_bought = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = " + str(cart_id))).fetchall()

    
    with db.engine.begin() as connection:
        total_potions_bought = 0
        for pot in potions_bought:
            print("Pot: " + str(pot))
            total_potions_bought += pot[7]

            connection.execute(sqlalchemy.text("INSERT INTO catalog (r,g,b,d,price,quantity,name) VALUES ("+str(pot[1])+", "+str(pot[2])+", "+str(pot[3])+", "+str(pot[4])+", "+str(pot[8])+", -"+str(pot[7])+", '"+str(pot[6])+"')"))
            params = {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'item_name': pot[6],
        'price': pot[8],
        'quantity': pot[7]
    }
            connection.execute(sqlalchemy.text("INSERT INTO invoices (customer_id, customer_name, item_sku, price, quantity, created_at) VALUES (:customer_id, :customer_name, :item_name, :price, :quantity, NOW())"), params)
            connection.execute(sqlalchemy.text("DELETE FROM cart_items WHERE sku = '" + str(pot[6]) + "'"))
                
        
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE id = " + str(cart_id) + ""))
        
            
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_price}
