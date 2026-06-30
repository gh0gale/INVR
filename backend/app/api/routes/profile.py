from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.profile import UserProfileRequest, UserProfileResponse
from app.api.deps import get_current_user_id
from app.services.profile_service import create_and_store_profile
from app.database import supabase_admin

router = APIRouter()

@router.get("/", response_model=UserProfileResponse)
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    try:
        # Query user profile from database
        res = supabase_admin.table("user_profiles").select("*").eq("id", user_id).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Error: {str(err)}")

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