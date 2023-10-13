from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from operator import itemgetter

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
def get_bottle_plan():              # FROM ALL THE POTIONS I MANUALLY CREATED IN CATALOG, MAKE
                                    # IT SO THAT QUANTITY IS ALWAYS THE SAME FOR ALL

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT * FROM catalog")).fetchall()
        ml = list(connection.execute(sqlalchemy.text("SELECT * FROM ml")).fetchall()[0][1:])
        print(ml)
    
    if ml[0] < 100 or ml[1] < 100 or ml[2] < 100:
        return []


    potions = sorted(potions, key=itemgetter(6))
    print(potions)

    potions_to_mix = []


    for i in range(len(potions)):
        if potions[i][6] != potions[0][6]:
            min_quantity = potions[i][6]
            break
    
    if min_quantity > 10:
        min_quantity = 10

    while potions != []:
        temp_ml = ml
        r, g, b, d = potions[0][1], potions[0][2], potions[0][3], potions[0][4]
        quant = 0
        while quant < min_quantity:
            if temp_ml[0] >= r and temp_ml[1] >= g and temp_ml[2] >= b and temp_ml[3] >= d:
                quant += 1
                temp_ml[0] -= r
                temp_ml[1] -= g
                temp_ml[2] -= b
                temp_ml[3] -= d
            else:
                break
        

        
        if quant != 0:
            potions_to_mix.append(
                {
                    "potion_type": [r, g, b, d],
                    "quantity": quant,
                })
        
        ml[0] -= r * quant
        ml[1] -= g * quant
        ml[2] -= b * quant
        ml[3] -= d * quant


        potions = potions[1:]
            
    
    return potions_to_mix
