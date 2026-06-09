from app.schemas.profile import UserProfileRequest, UserProfileResponse
from app.database import supabase_admin

def create_and_store_profile(user_id: str, payload: UserProfileRequest) -> UserProfileResponse:
    """
    Core business logic for processing and persisting a user profile.
    Separated from the HTTP layer for clean testing and reusability.
    """
    # 1. Extract hidden flags mapped during Pydantic validation
    contradictions = getattr(payload, "_contradictions_flagged", [])
    
    # 2. Generate the final hashed response object
    profile_response = UserProfileResponse.create_with_hash(
        request_data=payload, contradictions=contradictions
    )
    
    # 3. Prepare the database payload and inject the verified identity
    db_payload = profile_response.model_dump()
    db_payload["id"] = user_id
    
    # 4. Execute the database upsert bypassing RLS
    supabase_admin.table("user_profiles").upsert(db_payload).execute()
    
    return profile_response