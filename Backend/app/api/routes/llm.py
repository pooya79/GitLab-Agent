from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.db.models import User, Bot, Llm as LlmModel
from app.api.deps import SessionDep, get_current_user
from app.services.openrouter import OpenRouterClient, Model as OpenRouterModel
from app.schemas.llm import (
    OpenRouterModelsQuery,
    LlmCreate,
    LlmUpdate,
    LlmRead,
    LlmList,
)

router = APIRouter(prefix="/llms", tags=["llms"])


@router.get(
    "/openrouter_models",
    response_model=List[OpenRouterModel],
    summary="List OpenRouter models (optionally filtered)",
)
async def get_openrouter_models(
    params: OpenRouterModelsQuery = Depends(),
    current_user: User = Depends(get_current_user),
) -> List[OpenRouterModel]:
    """
    Fetch models from OpenRouter. If `query` is provided, only return models whose
    `id` or `name` contains the query string (case‑insensitive).
    """
    async with OpenRouterClient() as client:
        models = await client.get_models()

    # Keep only models with "tool" in supported_parameters
    filtered_models = []
    for m in models:
        supported_str = str(getattr(m, "supported_parameters", []))
        if "tool" in supported_str.lower():
            filtered_models.append(m)

    # Apply name/id query filter if provided
    if params.query:
        q = params.query.lower()
        filtered_models = [
            m
            for m in filtered_models
            if q in getattr(m, "id", "").lower() or q in getattr(m, "name", "").lower()
        ]

    return filtered_models


# ---------------------------
# LLM CRUD (async)
# ---------------------------


@router.post(
    "",
    response_model=LlmRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an LLM config",
)
async def create_llm(
    payload: LlmCreate,
    db: SessionDep,
    current_user: User = Depends(get_current_user),
) -> LlmRead:
    # Check unique name (friendly error)
    exists_res = await db.execute(
        select(func.count()).select_from(LlmModel).where(LlmModel.name == payload.name)
    )
    if exists_res.scalar_one():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An LLM with name '{payload.name}' already exists.",
        )

    entity = LlmModel(
        name=payload.name,
        model=payload.model,
        context_window=payload.context_window,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
        additional_kwargs=payload.additional_kwargs or {},
    )
    db.add(entity)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An LLM with name '{payload.name}' already exists.",
        )
    await db.refresh(entity)
    return LlmRead.model_validate(entity, from_attributes=True)


@router.get(
    "",
    response_model=LlmList,
    summary="List LLM configs (paginated)",
)
async def list_llms(
    db: SessionDep,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> LlmList:
    total_res = await db.execute(select(func.count()).select_from(LlmModel))
    total = total_res.scalar_one()

    rows_res = await db.execute(select(LlmModel).offset(skip).limit(limit))
    rows = rows_res.scalars().all()
    items = [LlmRead.model_validate(r, from_attributes=True) for r in rows]
    return LlmList(total=total, items=items)


@router.get(
    "/{llm_id}",
    response_model=LlmRead,
    summary="Get an LLM config by ID",
)
async def get_llm(
    llm_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_user),
) -> LlmRead:
    entity = await db.get(LlmModel, llm_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM not found"
        )
    return LlmRead.model_validate(entity, from_attributes=True)


@router.patch(
    "/{llm_id}",
    response_model=LlmRead,
    summary="Update an LLM config (partial)",
)
async def update_llm(
    llm_id: int,
    payload: LlmUpdate,
    db: SessionDep,
    current_user: User = Depends(get_current_user),
) -> LlmRead:
    entity = await db.get(LlmModel, llm_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM not found"
        )

    # Ensure unique name on change
    if payload.name and payload.name != entity.name:
        exists_res = await db.execute(
            select(func.count())
            .select_from(LlmModel)
            .where(LlmModel.name == payload.name)
        )
        if exists_res.scalar_one():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An LLM with name '{payload.name}' already exists.",
            )

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(entity, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update violates a uniqueness constraint.",
        )
    await db.refresh(entity)
    return LlmRead.model_validate(entity, from_attributes=True)


@router.delete(
    "/{llm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an LLM config",
)
async def delete_llm(
    llm_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_user),
) -> None:
    entity = await db.get(LlmModel, llm_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM not found"
        )

    # Check if any Bot uses this LLM
    result = await db.execute(select(Bot).where(Bot.llm_id == llm_id))
    bot_using_llm = result.scalar_one_or_none()
    if bot_using_llm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete LLM because one or more bots are using it.",
        )

    await db.delete(entity)
    await db.commit()
    return None
