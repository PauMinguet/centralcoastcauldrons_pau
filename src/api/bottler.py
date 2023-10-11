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
    ml_delivered = [0,0,0,0]
    for pot in potions_delivered:
        for i in range(4):
            ml_delivered[i] += pot.potion_type[i] * pot.quantity
    
    print(ml_delivered)
    

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM ml"))
    ml = list(result.fetchall()[0])[1:]

    print(ml)

    final_ml = [ml[0] - ml_delivered[0], ml[1] - ml_delivered[1], ml[2] - ml_delivered[2], ml[3] - ml_delivered[3]]

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE ml SET redml = " + str(final_ml[0])))
        result = connection.execute(sqlalchemy.text("UPDATE ml SET greenml = " + str(final_ml[1])))
        result = connection.execute(sqlalchemy.text("UPDATE ml SET blueml = " + str(final_ml[2])))
        result = connection.execute(sqlalchemy.text("UPDATE ml SET tranml = " + str(final_ml[3])))


    for pot in potions_delivered:
        color = "potion_" + str(pot.potion_type[0]) + "_" + str(pot.potion_type[1]) + "_" + str(pot.potion_type[2]) + "_" + str(pot.potion_type[3])
        with db.engine.begin() as connection:
            potion = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE name= '" + color + "'")).first()
            #print(potion)
            #print("potion above")
        if potion != None:
            #print(potion[6])
            #print(pot.quantity)
            final_num_potion = int(potion[6]) + int(pot.quantity)
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE catalog SET quantity = " + str(final_num_potion) + " WHERE name = '" + color +"'"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM ml"))

    ml = result.first()[1:]

    potions_to_mix = []

    for i in range(len(ml)):
        if ml[i] > 100:
            potions_to_mix.append(
            {
                "potion_type": [100 if i==0 else 0, 100 if i==1 else 0, 100 if i==2 else 0, 100 if i==3 else 0],
                "quantity": ml[i] // 100,
            })
    
    return potions_to_mix
