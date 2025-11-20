"""
Database Schemas for Agency Campaign Management

Collections:
- Client: agency clients
- Campaign: marketing campaigns linked to a client
- MediaPlanItem: budget allocations per channel/vendor per campaign
- ActionItem: tasks/acciones linked to a campaign
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class Client(BaseModel):
    name: str = Field(..., description="Nombre del cliente")
    contact_name: Optional[str] = Field(None, description="Persona de contacto")
    email: Optional[str] = Field(None, description="Email del cliente")
    phone: Optional[str] = Field(None, description="Teléfono")
    notes: Optional[str] = Field(None, description="Notas")

class Campaign(BaseModel):
    client_id: str = Field(..., description="ID del cliente")
    name: str = Field(..., description="Nombre de la campaña")
    start_date: Optional[date] = Field(None, description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    budget_total: float = Field(0, ge=0, description="Presupuesto total")
    status: Literal["planificada", "activa", "pausada", "finalizada"] = Field("planificada", description="Estado de la campaña")
    objective: Optional[str] = Field(None, description="Objetivo de la campaña")

class MediaPlanItem(BaseModel):
    campaign_id: str = Field(..., description="ID de la campaña")
    channel: str = Field(..., description="Medio/canal (Ej: Facebook Ads, Google, TV)")
    vendor: Optional[str] = Field(None, description="Proveedor")
    budget_allocated: float = Field(0, ge=0, description="Presupuesto asignado")
    notes: Optional[str] = Field(None, description="Notas")

class ActionItem(BaseModel):
    campaign_id: str = Field(..., description="ID de la campaña")
    title: str = Field(..., description="Acción/Tarea")
    owner: Optional[str] = Field(None, description="Responsable")
    due_date: Optional[date] = Field(None, description="Fecha límite")
    status: Literal["pendiente", "en progreso", "hecha", "bloqueada"] = Field("pendiente", description="Estado")
    cost_actual: Optional[float] = Field(None, ge=0, description="Costo real (opcional)")
