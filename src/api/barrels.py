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
    
    purchase_price = barrels_delivered[0].price
    ml_in_barrel = barrels_delivered[0].ml_per_barrel
    type = barrels_delivered[0].potion_type
    
    # FIND OUT COLOR OF BARREL
    colorml = None
    if type[0] == 1:
        colorml = "redml"
    elif type[1] == 1:
        colorml = "greenml"
    elif type[2] == 1:
        colorml = "blueml"
    elif type[3] == 1:
        colorml = "tranml"


    # UPDATE GOLD
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
    gold = result.first()[0]
    
    final_gold = gold - purchase_price

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(final_gold)))



    with db.engine.begin() as connection:
        ml_to_update = connection.execute(sqlalchemy.text("SELECT " + colorml + " FROM ml")).first()[0]
    ml_to_update += ml_in_barrel
    

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE ml SET " + colorml + " = " + str(ml_to_update)))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    barrel_cart = []

    rgbt = [0,0,0,0]
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM catalog")).fetchall()
    print(inventory)

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]

                        # for now just buy one small barrel (much better value than the tiny ones) of the color that we 
                        # have the least either in potions or in ml, since bottler will make the max amount of every color potion


    for item in (inventory):
        rgbt[0] += item[1] * item[6]
        rgbt[1] += item[2] * item[6]
        rgbt[2] += item[3] * item[6]
        rgbt[3] += item[4] * item[6]

    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text("SELECT * FROM ml")).first()

    for i in range(1, len(ml)-1):
        rgbt[i] += ml[i+1]

    barrel_order = [0,0,0]

    while gold >= 120:

        min_ml = 1000000
        min_col = 3
        for i in range(3):
            if rgbt[i] < min_ml:
                min_ml = rgbt[i]
                min_col = i
        
        if min_col == 0:
            barrel_order[0] += 1
            rgbt[0] += 500
            gold -= 100
        elif min_col == 1:
            barrel_order[1] += 1
            rgbt[1] += 500
            gold -= 120
        elif min_col == 2:
            barrel_order[2] += 1
            rgbt[2] += 500
            gold -= 120
        else:
            least = None

        #print(rgbt)
        #print(least)


    colors = ["RED", "GREEN", "BLUE"]
    for i in range(len(barrel_order)):
        if barrel_order[i] != 0:
            barrel_cart.append({
        "sku": "SMALL_" + colors[i] + "_BARREL",
        "quantity": barrel_order[i],
    })
    
    

    return barrel_cart