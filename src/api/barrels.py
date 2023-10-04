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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
    gold = result.first()[0]
    
    final_gold = gold - purchase_price

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(final_gold)))



    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    red_ml = result.first()[0]
    
    final_red_ml = red_ml + ml_in_barrel

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(final_red_ml)))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
    
    pots = result.first()[0]
    print(pots)

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1 if pots < 10 else 0,
        }
    ]
