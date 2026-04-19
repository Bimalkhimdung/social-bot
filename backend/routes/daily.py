"""Daily NEPSE market update post routes."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routes.auth import get_current_user

router = APIRouter(prefix="/api/daily", tags=["daily"])


@router.get("/preview-card", response_class=Response)
async def preview_daily_card():
    """Generate and return the NEPSE daily card as a JPEG image."""
    from image_card.nepse_daily_card import generate_nepse_daily_card
    try:
        card_bytes = await generate_nepse_daily_card()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Card generation failed: {exc}")
    return Response(
        content=card_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


@router.post("/post-now")
async def post_daily_to_facebook(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    """Generate the NEPSE daily card and publish it to Facebook."""
    from image_card.nepse_daily_card import generate_nepse_daily_card, _nepali_date_str
    from publisher.facebook import publisher

    try:
        card_bytes = await generate_nepse_daily_card()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Card generation failed: {exc}")

    # Upload photo
    photo_id = None
    if publisher.is_configured:
        photo_id = await publisher.upload_photo(db, card_bytes)
        if not photo_id:
            raise HTTPException(status_code=500, detail="Photo upload to Facebook failed.")

    # Build caption in Nepali
    date_str = _nepali_date_str()
    caption = (
        f"📊 आजको नेप्से बजार सारांश | {date_str}\n\n"
        f"📈 नेप्से इन्डेक्स, कुल कारोबार र कारोबार भएका शेयरको विवरण तलको कार्डमा हेर्नुहोस्।\n\n"
        f"#NEPSE #नेप्से #ShareMarket #Nepal #StockMarket #सेयर #लगानी"
    )

    fb_post_id = await publisher.publish(
        db,
        title=f"नेप्से दैनिक अपडेट — {date_str}",
        article_url="https://sharehubnepal.com",
        caption=caption,
        photo_id=photo_id,
        dry_run=not publisher.is_configured,
    )

    if not fb_post_id and publisher.is_configured:
        raise HTTPException(status_code=500, detail="Facebook publication failed. Check backend logs.")

    return {
        "success": True,
        "fb_post_id": fb_post_id,
        "dry_run": not publisher.is_configured,
        "date": date_str,
    }

class CustomPostRequest(BaseModel):
    text: str


@router.post("/preview-custom-card", response_class=Response)
async def preview_custom_card(payload: CustomPostRequest):
    """Generate and return the custom NEPSE card as a JPEG image."""
    from image_card.nepse_daily_card import generate_custom_card
    try:
        card_bytes = await generate_custom_card(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Card generation failed: {exc}")
    return Response(
        content=card_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


@router.post("/post-custom")
async def post_custom_to_facebook(
    payload: CustomPostRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[str, Depends(get_current_user)],
):
    """Generate the custom NEPSE card and publish it to Facebook."""
    from image_card.nepse_daily_card import generate_custom_card, _nepali_date_str
    from publisher.facebook import publisher

    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Custom text cannot be empty.")

    try:
        card_bytes = await generate_custom_card(payload.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Card generation failed: {exc}")

    # Upload photo
    photo_id = None
    if publisher.is_configured:
        photo_id = await publisher.upload_photo(db, card_bytes)
        if not photo_id:
            raise HTTPException(status_code=500, detail="Photo upload to Facebook failed.")

    # Build caption
    date_str = _nepali_date_str()
    caption = (
        f"📊 विशेष अपडेट | {date_str}\n\n"
        f"{payload.text}\n\n"
        f"#NEPSE #नेप्से #ShareMarket #Nepal #StockMarket #सेयर #लगानी"
    )

    fb_post_id = await publisher.publish(
        db,
        title=f"नेप्से विशेष अपडेट — {date_str}",
        article_url="https://sharehubnepal.com",
        caption=caption,
        photo_id=photo_id,
        dry_run=not publisher.is_configured,
    )

    if not fb_post_id and publisher.is_configured:
        raise HTTPException(status_code=500, detail="Facebook publication failed. Check backend logs.")

    return {
        "success": True,
        "fb_post_id": fb_post_id,
        "dry_run": not publisher.is_configured,
        "date": date_str,
    }
