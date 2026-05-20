from fastapi import APIRouter, Request, Response

from app.deps import CurrentUser, DBSession
from app.modules.billing import service
from app.modules.billing.schemas import (
    BillingPortalResponse,
    BillingSessionResponse,
    BillingStatusResponse,
)

router = APIRouter()
webhook_router = APIRouter()


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(current_user: CurrentUser, db: DBSession):
    return await service.get_billing_status(db, current_user.id)


@router.post("/checkout", response_model=BillingSessionResponse, status_code=201)
async def create_checkout_session(current_user: CurrentUser, db: DBSession):
    return await service.create_checkout_session(db, current_user.id)


@router.post("/portal", response_model=BillingPortalResponse, status_code=201)
async def create_billing_portal(current_user: CurrentUser, db: DBSession):
    return await service.create_billing_portal_session(db, current_user.id)


@webhook_router.post("/webhook")
async def stripe_webhook(request: Request, db: DBSession):
    await service.handle_webhook(db, request)
    response = Response(content='{"received":true}', media_type="application/json")
    response.headers["X-No-Envelope"] = "1"
    return response
