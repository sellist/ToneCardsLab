from fastapi import APIRouter, Depends

from tcl_api.models.music import Note
from tcl_api.models.response import ApiResponse, ResponseBuilder
from tcl_api.services.note_service import NoteService, note_service

router = APIRouter(prefix="/note", tags=["note"])

def get_note_service() -> NoteService:
    return note_service

@router.get("/aspn", response_model=ApiResponse[Note])
def health_check(aspn: str, service: NoteService = Depends(get_note_service)) -> ApiResponse[Note]:
    return ResponseBuilder(service.get_note_from_aspn(aspn)).build()
