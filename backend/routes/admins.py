from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import AdminRequest, AdminsResponse
from ..repositories import add_admin, list_admins, remove_admin
from ..security import require_admin, require_super_admin

router = APIRouter(prefix="/admins", tags=["admin"])


@router.get("", response_model=AdminsResponse)
async def get_admins(user=Depends(require_admin)) -> AdminsResponse:  # type: ignore[unused-ignore]
    admins = await list_admins()
    return AdminsResponse(admins=admins)


@router.post("", response_model=AdminsResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(body: AdminRequest, user=Depends(require_super_admin)) -> AdminsResponse:  # type: ignore[unused-ignore]
    if not body.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username obbligatorio")
    admins = await add_admin(body.username)
    return AdminsResponse(admins=admins)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(username: str, user=Depends(require_super_admin)) -> None:  # type: ignore[unused-ignore]
    await remove_admin(username)
