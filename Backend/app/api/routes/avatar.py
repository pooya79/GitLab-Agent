from pathlib import Path

from fastapi import APIRouter, Depends
from app.schemas.avatar import AvatarList, AvatarItem
from app.db.models import User
from app.api.deps import get_current_user

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
AVATARS_SUBDIR = "avatars"

router = APIRouter(
    prefix="/avatars",
    tags=["avatars"],
)


def _avatars_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "assets" / AVATARS_SUBDIR


@router.get("/", response_model=AvatarList)
async def list_available_avatars(
    current_user: User = Depends(get_current_user),
) -> AvatarList:
    root = _avatars_dir()
    if not root.exists():
        return AvatarList(items=[])
    items: list[AvatarItem] = []
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            stat = p.stat()
            items.append(
                AvatarItem(
                    name=p.name,
                    url=f"/api/static/avatars/{p.name}",
                    size_bytes=stat.st_size,
                    modified_ts=stat.st_mtime,
                )
            )
    return AvatarList(items=items)
