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
        connection.execute(sqlalchemy.text("INSERT INTO inventory (r, g, b, d) VALUES (-"+str(ml_delivered[0])+", -"+str(ml_delivered[1])+", -"+str(ml_delivered[2])+", -"+str(ml_delivered[1])+")"))


    for pot in potions_delivered:
        color = "potion_" + str(pot.potion_type[0]) + "_" + str(pot.potion_type[1]) + "_" + str(pot.potion_type[2]) + "_" + str(pot.potion_type[3])
        with db.engine.begin() as connection:
            potion = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE name= '" + color + "'")).first()
            connection.execute(sqlalchemy.text("INSERT INTO potion_orders (name, quantity) VALUES ('" + color +"', " + str(pot.quantity) + ")"))
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

    potions_to_mix = []

    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT * FROM catalog")).fetchall()
        ml = list(connection.execute(sqlalchemy.text("SELECT SUM(r), SUM(g), SUM(b), SUM(d) FROM inventory")).first())
        print(ml)
    
    for i in range(len(potions)):
        potions[i] = list(potions[i])
    
    while potions != []:
        potions = sorted(potions, key=itemgetter(6))
        print(potions)
        if canMake(ml, potions[0]):
            ml, potions, potions_to_mix = makePotion(ml, potions, potions_to_mix)
        else:
            potions = potions[1:]

    return potions_to_mix


def canMake(ml, pot):
    if ml[0] >= pot[1] and ml[1] >= pot[2] and ml[2] >= pot[3] and ml[3] >= pot[4]:
        return True
    return False

def makePotion(ml, potions, potions_to_mix):
    pot = potions[0]
    #print(pot)
    ml[0] -= pot[1]
    ml[1] -= pot[2]
    ml[2] -= pot[3]
    ml[3] -= pot[4]

    pot_type = [pot[1], pot[2], pot[3], pot[4]]

    done = False

    for poti in potions_to_mix:
        if poti["potion_type"] == pot_type:
            poti["quantity"] += 1
            done = True
            break
    if not done:
        potions_to_mix.append(
                {
                    "potion_type": pot_type,
                    "quantity": 1,
                })

    potions[0][6] += 1

    return ml, potions, potions_to_mix