from pydantic import BaseModel


class BillingSessionResponse(BaseModel):
    url: str


class BillingPortalResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    configured: bool
    has_active_subscription: bool
    plan_type: str
    subscription_status: str | None = None
