from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@router.get("/readyz")
async def readyz() -> dict:
    # Phase 0 先固定回 OK
    # Phase 1/2 起會把 DB/tool registry 初始化狀態納入 readiness
    return {"ready": True}
