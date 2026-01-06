from pydantic.fields import Field
from typing import Dict, Optional
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    status: str = Field(..., description="Status of the service", example="ok")
    message: Optional[str] = Field(None, description="Status message", example="Connected successfully")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Status of the application", example="ok")
    version: str = Field(..., description="Version of the application", example="0.1.0")
    environment: str = Field(..., description="Environment of the application", example="development")
    service_name: str = Field(..., description="Name of the service", example="rag-api")
    services: Optional[Dict[str, ServiceStatus]] = Field(None, description="Individual service statuses")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "environment": "development",
                "service_name": "rag-api",
                "services": {
                    "database": {"status": "healthy", "message": "Connected successfully"},
                }
            }
        }