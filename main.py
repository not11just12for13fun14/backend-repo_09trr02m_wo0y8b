import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Client, Campaign, MediaPlanItem, ActionItem

app = FastAPI(title="Agency Campaign Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Agency Campaign Manager API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Helper to convert string id to ObjectId filter safely

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# Basic list endpoints using the helper get_documents

@app.get("/clients")
def list_clients():
    return get_documents("client")

@app.post("/clients")
def create_client(payload: Client):
    new_id = create_document("client", payload)
    return {"inserted_id": new_id}

@app.get("/campaigns")
def list_campaigns(client_id: Optional[str] = None):
    filt = {"client_id": client_id} if client_id else {}
    return get_documents("campaign", filt)

@app.post("/campaigns")
def create_campaign(payload: Campaign):
    # validate that client exists if provided
    if payload.client_id:
        existing = db["client"].find_one({"_id": oid(payload.client_id)}) if ObjectId.is_valid(payload.client_id) else None
        if existing is None:
            raise HTTPException(status_code=404, detail="Client not found")
    new_id = create_document("campaign", payload)
    return {"inserted_id": new_id}

@app.get("/media-plan")
def list_media_plan(campaign_id: Optional[str] = None):
    filt = {"campaign_id": campaign_id} if campaign_id else {}
    return get_documents("mediaplanitem", filt)

@app.post("/media-plan")
def create_media_plan_item(payload: MediaPlanItem):
    # check campaign exists
    if payload.campaign_id:
        existing = db["campaign"].find_one({"_id": oid(payload.campaign_id)}) if ObjectId.is_valid(payload.campaign_id) else None
        if existing is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
    new_id = create_document("mediaplanitem", payload)
    return {"inserted_id": new_id}

@app.get("/actions")
def list_actions(campaign_id: Optional[str] = None):
    filt = {"campaign_id": campaign_id} if campaign_id else {}
    return get_documents("actionitem", filt)

@app.post("/actions")
def create_action(payload: ActionItem):
    if payload.campaign_id:
        existing = db["campaign"].find_one({"_id": oid(payload.campaign_id)}) if ObjectId.is_valid(payload.campaign_id) else None
        if existing is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
    new_id = create_document("actionitem", payload)
    return {"inserted_id": new_id}

# Simple rollup: budget summary per campaign

class BudgetSummary(BaseModel):
    campaign_id: str
    budget_total: float
    allocated: float
    remaining: float

@app.get("/campaigns/{campaign_id}/budget", response_model=BudgetSummary)
def campaign_budget(campaign_id: str):
    camp = db["campaign"].find_one({"_id": oid(campaign_id)})
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")
    total = float(camp.get("budget_total", 0))
    allocated = 0.0
    for item in db["mediaplanitem"].find({"campaign_id": campaign_id}):
        allocated += float(item.get("budget_allocated", 0))
    remaining = max(total - allocated, 0.0)
    return BudgetSummary(campaign_id=campaign_id, budget_total=total, allocated=allocated, remaining=remaining)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
