from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    
    if len(barrels_delivered) == 0:
        return "Nothing Delivered"
    
    for i in range(len(barrels_delivered)):

        purchase_price = barrels_delivered[i].price
        ml_in_barrel = barrels_delivered[i].ml_per_barrel
        type = barrels_delivered[i].potion_type
        quantity = barrels_delivered[i].quantity
        
        # FIND OUT COLOR OF BARREL
        colorml = None
        if type[0] == 1:
            colorml = "redml"
        elif type[1] == 1:
            colorml = "greenml"
        elif type[2] == 1:
            colorml = "blueml"
        elif type[3] == 1:
            colorml = "darkml"


        # UPDATE GOLD
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold = result.first()[0]
        
        final_gold = gold - purchase_price * quantity

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(final_gold)))
            connection.execute(sqlalchemy.text("UPDATE ml SET " + colorml + " = " + colorml + " + " + str(ml_in_barrel * quantity)))
            connection.execute(sqlalchemy.text("INSERT INTO barrel_orders (color, size, price, quantity) VALUES ('" + colorml + "', " + str(ml_in_barrel) + " , " + str(purchase_price) + ", " + str(quantity) +")"))


    return "OK"











# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        ml = list(connection.execute(sqlalchemy.text("SELECT * FROM ml")).first()[1:])

    print(ml)

    wholesale_catalog = sorted(wholesale_catalog, key= lambda ele: ele.ml_per_barrel, reverse=True)
    
    large_barrels, medium_barrels, small_barrels = [], [], []
    for barrel in wholesale_catalog:
        if barrel.ml_per_barrel == 10000:
            large_barrels.append(barrel)
        elif barrel.ml_per_barrel == 2500:
            medium_barrels.append(barrel)
        elif barrel.ml_per_barrel == 500:
            small_barrels.append(barrel)
    
    '''print("LARGE BARRELS")
    print(large_barrels)
    print()
    print("MEDIUM BARRELS")
    print(medium_barrels)
    print()
    print("SMALL BARRELS")
    print(small_barrels)
    print()'''

    barrel_cart = []

    
    all_barrels = [large_barrels, medium_barrels, small_barrels]

    for i in range(3):
        in_progress = all_barrels[i]
        if in_progress == []:
            continue
        size_name = all_barrels[i][0].sku.split("_")[0]
        ordered = [0,0,0,0]
        prices = [i.price for i in in_progress]
        colors = [i.sku.split("_")[1] for i in in_progress]

        #print(prices)
        #print(colors)

        while gold > max(prices):
            min_ml = ml[0]
            min_col = 0
            for i in range(1,len(colors)):
                if ml[i] < min_ml:
                    min_ml = ml[i]
                    min_col = i

            ordered[min_col] += 1
            ml[min_col] += in_progress[0].ml_per_barrel
            gold -= prices[min_col]
                

        for i in range(len(ordered)):
            if ordered[i] != 0:
                barrel_cart.append({
            "sku": size_name + "_" + colors[i] + "_BARREL",
            "quantity": ordered[i] if ordered[i] < 10 else 10,
        })
            
    print(ml)
    return barrel_cart