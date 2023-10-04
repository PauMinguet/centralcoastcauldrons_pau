from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    
    num_red_potions_delivered = 0

    for i in range(len(potions_delivered)):
        if potions_delivered[i].potion_type == [100, 0, 0, 0]:
            num_red_potions_delivered += potions_delivered[i].quantity

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    ml = result.first()[0]

    red_ml_tosubtract = ml - num_red_potions_delivered * 100

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(red_ml_tosubtract)))


    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
    num_red_potions = result.first()[0]

    final_num_red_potions = num_red_potions + num_red_potions_delivered

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(final_num_red_potions)))


    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    
    ml = result.first()[0]

    print(ml)

    num_red_potions_mix = ml // 100

    
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_red_potions_mix,
            }
        ]
