"""RSS subscription endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.apps.api.dependencies import get_rss_repository
from src.apps.api.schemas import RSSSubscriptionCreateRequest, RSSSubscriptionCreateResponse
from src.core.utils.url import build_youtube_channel_feed_url
from src.services.rss.subscription_service import create_rss_subscription

router = APIRouter()


@router.post(
    "/rss/subscriptions",
    response_model=RSSSubscriptionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rss_subscription_endpoint(
    payload: RSSSubscriptionCreateRequest,
) -> RSSSubscriptionCreateResponse:
    """Create a YouTube RSS channel subscription in SQLite."""

    repository = get_rss_repository()
    feed_url = payload.feed_url or build_youtube_channel_feed_url(payload.channel_id)
    try:
        result = create_rss_subscription(
            repository,
            channel_id=payload.channel_id,
            feed_url=feed_url,
            title=payload.title or "",
            enabled=payload.enabled,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_409_CONFLICT if "已存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create RSS subscription.",
        ) from exc

    return RSSSubscriptionCreateResponse(
        subscription_id=result.subscription_id or "",
        channel_id=result.channel_id,
        feed_url=result.feed_url,
        title=result.title,
        enabled=result.enabled,
        message=result.message,
    )



