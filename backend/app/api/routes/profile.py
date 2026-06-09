from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.profile import UserProfileRequest, UserProfileResponse
from app.api.deps import get_current_user_id
from app.services.profile_service import create_and_store_profile

router = APIRouter()

@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def ingest_user_profile(
    payload: UserProfileRequest, 
    user_id: str = Depends(get_current_user_id)
):
    try:
        # Delegate all heavy lifting to the service layer
        return create_and_store_profile(user_id=user_id, payload=payload)

    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as db_err:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(db_err)}")