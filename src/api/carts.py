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
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    with db.engine.begin() as connection:
        params = {
            customer_name_filter: '',
            potion_sku_filter: '',
            sort_col: sort_col,
            sort_order: sort_order
        }
        
        if customer_name != '':
            customer_name_filter = 'WHERE customer_name = ' + customer_name
        if potion_sku != '':
            potion_sku_filter = 'WHERE potion_sku = ' + potion_sku
        if sort_col != '':
            sort_col_filter = 'ORDER BY ' + sort_col

        connection.execute(sqlalchemy.text("""
        SELECT created_at AS timestamp, customer_name, item_sku, quantity * price AS line_item_total FROM invoices
        :customer_name_filter
        :potion_sku_filter
        ORDER BY :sort_col
        
        """, params))



    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }





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
