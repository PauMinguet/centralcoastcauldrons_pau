from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():                #   NOT UPDATED FOR 3 COLORS OR FOR NEW TABLES
    """ """

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM gold")).first()[0]
        num_pots = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).scalar_one()
        ml = list(connection.execute(sqlalchemy.text("SELECT SUM(r), SUM(g), SUM(b), SUM(d) FROM inventory")).first())
    
    num_ml = 0
    for m in ml:
        num_ml += m
    
    print(num_pots, num_ml, gold)
    
    
    return {"number_of_potions": num_pots, "ml_in_barrels": num_ml, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
