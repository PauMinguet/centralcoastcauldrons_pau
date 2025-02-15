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
        connection.execute(sqlalchemy.text("INSERT INTO inventory (r, g, b, d) VALUES (-"+str(ml_delivered[0])+", -"+str(ml_delivered[1])+", -"+str(ml_delivered[2])+", -"+str(ml_delivered[3])+")"))


    with db.engine.begin() as connection:
        for pot in potions_delivered:
            color = "potion_" + str(pot.potion_type[0]) + "_" + str(pot.potion_type[1]) + "_" + str(pot.potion_type[2]) + "_" + str(pot.potion_type[3])
            potion_sample = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE name = '" + color + "'")).first()

            print(potion_sample)

            connection.execute(sqlalchemy.text("INSERT INTO potion_orders (name, quantity) VALUES ('" + color +"', " + str(pot.quantity) + ")"))

            connection.execute(sqlalchemy.text("INSERT INTO catalog (r, g, b, d, price, quantity, name) VALUES (" + str(pot.potion_type[0]) + "," + str(pot.potion_type[1]) + "," + str(pot.potion_type[2]) + "," + str(pot.potion_type[3]) + ", " + str(potion_sample[5]) + ", " + str(pot.quantity) + ", '" + color + "')"))

    return "OK"






# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():              # FROM ALL THE POTIONS I MANUALLY CREATED IN CATALOG, MAKE
                                    # IT SO THAT QUANTITY IS ALWAYS THE SAME FOR ALL
    potions_to_mix = []

    with db.engine.begin() as connection:
        num_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).scalar_one()
        wishlist = connection.execute(sqlalchemy.text("SELECT name, quantity FROM wishlist")).fetchall()
        potions = connection.execute(sqlalchemy.text("SELECT r,g,b,d,price,SUM(quantity),name FROM catalog GROUP BY r, g, b, d, price, name")).fetchall()
        ml = list(connection.execute(sqlalchemy.text("SELECT SUM(r), SUM(g), SUM(b), SUM(d) FROM inventory")).first())
        print(ml)
        print(potions)
    
    for i in range(len(potions)):
        potions[i] = list(potions[i])
    
    while potions != []:
        if num_potions > 290:
            break
        potions = sorted(potions, key=itemgetter(5))
        if canMake(ml, potions[0]):
            ml, potions, potions_to_mix = makePotion(ml, potions, potions_to_mix)
            num_potions += 1
        else:
            potions = potions[1:]

    return potions_to_mix


def canMake(ml, pot):
    if ml[0] >= pot[0] and ml[1] >= pot[1] and ml[2] >= pot[2] and ml[3] >= pot[3]:
        return True
    return False

def makePotion(ml, potions, potions_to_mix):
    pot = potions[0]
    #print(pot)
    ml[0] -= pot[0]
    ml[1] -= pot[1]
    ml[2] -= pot[2]
    ml[3] -= pot[3]

    pot_type = [pot[0], pot[1], pot[2], pot[3]]

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

    potions[0][5] += 1

    return ml, potions, potions_to_mix