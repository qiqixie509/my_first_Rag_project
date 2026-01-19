from src.schemas.api.health import ServiceStatus
from fastapi import APIRouter
from sqlalchemy import text
from src.schemas.api.health import HealthResponse
from src.dependencies import DatabaseDep, SettingsDep

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(settings: SettingsDep, database: DatabaseDep):
    services = {}
    overall_status = "ok"
    
    def _check_service(name: str, check_func, *args, **kwargs):
        try:
            if kwargs.get("is_async"):
                return check_func(*args)
            result = check_func(*args)
            services[name] = result
            if result.status != "healthy":
                nonlocal overall_status
                overall_status = "degraded"
            else:
                return check_func(*args, **kwargs)
        except Exception as e:
            services[name] = ServiceStatus(status="unhealthy", message=str(e))
            overall_status = "degraded"

    def _check_database():
        with database.get_session() as session:
            session.execute(text("SELECT 1"))
            return ServiceStatus(status="healthy", message="Database connection successful") 
        


    _check_service("database", _check_database)
    return HealthResponse(
        status=overall_status, 
        version=settings.app_version,
        environment=settings.enviornment,
        service_name=settings.service_name,
        services=services
    )