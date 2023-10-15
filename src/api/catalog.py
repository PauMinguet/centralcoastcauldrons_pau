from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():                              # START THINKING ABOUT CUSTOMER LIKES AND DISLIKES AND
                                                # PRICE RANGE TO CUSTOMIZE CATALOG AND MAKE MORE $$$

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM catalog WHERE quantity > 0"))
    pots = result.fetchall()[:19] # Can return a max of 20 items.
    print(pots)

    catalog = []

    for pot in pots:
        color = "potion_" + str(pot[1]) + "_" + str(pot[2]) + "_" + str(pot[3]) + "_" + str(pot[4])
        catalog.append(
            {
                "sku": color,
                "name": color,
                "quantity": str(pot[6]),
                "price": str(pot[5]),
                "potion_type": [pot[1], pot[2], pot[3], pot[4]],
            }
        )

    return catalog
