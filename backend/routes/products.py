from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import ProductCreate, ProductResponse, ProductsResponse, ProductUpdate
from ..repositories import delete_product, get_product, list_products, save_product
from ..security import require_admin
from ..utils import nano_id

router = APIRouter(prefix="/products", tags=["prodotti"])


@router.get("", response_model=ProductsResponse)
async def get_products(category: str | None = None) -> ProductsResponse:
    items = await list_products(category)
    return ProductsResponse(items=items)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(product_id: str) -> ProductResponse:
    product = await get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prodotto non trovato")
    return ProductResponse(item=product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, user=Depends(require_admin)) -> ProductResponse:  # type: ignore[unused-ignore]
    product_id = payload.id or nano_id()
    product = await save_product({
        "id": product_id,
        "name": payload.name,
        "category": payload.category,
        "media": payload.media,
        "description": payload.description,
        "featured": payload.featured,
    })
    return ProductResponse(item=product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, payload: ProductUpdate, user=Depends(require_admin)) -> ProductResponse:  # type: ignore[unused-ignore]
    existing = await get_product(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prodotto non trovato")
    updated = await save_product({
        "id": product_id,
        "name": payload.name or existing["name"],
        "category": payload.category or existing["category"],
        "media": payload.media or existing["media"],
        "description": payload.description or existing["description"],
        "featured": existing["featured"] if payload.featured is None else payload.featured,
    })
    return ProductResponse(item=updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(product_id: str, user=Depends(require_admin)) -> None:  # type: ignore[unused-ignore]
    product = await get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prodotto non trovato")
    await delete_product(product_id)
