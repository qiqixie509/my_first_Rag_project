from ensurepip import version
from pydantic.fields import Field
from typing import Dict, Optional


class ServiceStatus(BaseModel):
    status: str = Field(..., description="Status of the service", example="ok")
    environment: str = Field(..., description="Environment of the service", example="development")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Status of the application", example="ok")
    version: str = Field(..., description="Version of the application", example="0.1.0")
    environment: str = Field(..., description="Environment of the application", example="development")
    service_name: str = Field(..., description="Name of the service", example="rag-api")
    services: Optional[Dict[str, ServiceStatus]] = Field(description="Status of the services")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "environment": "development",
                "service_name": "rag-api",
                "services": {
                    "postgres": {
                        "status": "ok",
                        "environment": "development"
                    },
                    "opensearch": {
                        "status": "ok",
                        "environment": "development"
                    },
                    "ollama": {
                        "status": "ok",
                        "environment": "development"
                    }
                }
            }
        }