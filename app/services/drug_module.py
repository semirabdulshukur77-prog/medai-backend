# backend/app/services/drug_module.py

from app.db import get_db
from typing import List, Dict

def check_drug_interactions(drugs: List[str]) -> List[Dict[str, str]]:
    """
    Check drug interactions using DB.
    """
    db = get_db()
    interactions = []
    for i, drug1 in enumerate(drugs):
        for drug2 in drugs[i+1:]:
            rows = db.execute(
                """
                SELECT * FROM drug_interactions
                WHERE (drug1=? AND drug2=?) OR (drug1=? AND drug2=?)
                """,
                (drug1, drug2, drug2, drug1)
            ).fetchall()
            for row in rows:
                interactions.append({
                    "drug1": row["drug1"],
                    "drug2": row["drug2"],
                    "interaction": row["interaction"]
                })
    return interactions

