from fastapi import APIRouter
import sqlalchemy
from src import database as db
from operator import itemgetter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():                              # START THINKING ABOUT CUSTOMER LIKES AND DISLIKES AND
                                                # PRICE RANGE TO CUSTOMIZE CATALOG AND MAKE MORE $$$

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT DISTINCT c.name, s.total_quantity AS quantity, c.price, c.r, c.g, c.b, c.d
            FROM catalog c
            INNER JOIN (
                SELECT name, SUM(quantity) AS total_quantity
                FROM catalog
                GROUP BY name
            ) s ON c.name = s.name
            ORDER BY s.total_quantity DESC                  
            """))
        
    pots = result.fetchall()[:6] # Can return a max of 20 items.

    print(pots)
    catalog = []

    for pot in pots:
        #if pot[1] != 0:
            catalog.append(
            {
                "sku": pot[0],
                "name": pot[0],
                "quantity": pot[1],
                "price": pot[2],
                "potion_type": [pot[3], pot[4], pot[5], pot[6]],
            }
        )

    return catalog
