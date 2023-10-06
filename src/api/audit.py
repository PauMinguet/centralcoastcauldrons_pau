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
        gold1 = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        pots1 = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        ml1 = connection.execute(sqlalchemy.text("SELECT num_ml FROM global_inventory"))
    gold = gold1.first()[0]
    pots = pots1.first()[0]
    ml = ml1.first()[0]
    
    return {"number_of_potions": pots, "ml_in_barrels": ml, "gold": gold}

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
