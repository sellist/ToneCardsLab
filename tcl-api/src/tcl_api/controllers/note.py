from fastapi import Query
from tcl_api.models import ApiResponse
from tcl_api.models.music import Note
from tcl_api.services.note import note_service
from tcl_api.controllers.base import BaseController

NoteApiResponse = ApiResponse[Note]

class NoteController(BaseController[Note]):
    def __init__(self):
        super().__init__(prefix="/note", tags=["note"], controller_name="note")

    def _register_routes(self):
        self.router.add_api_route("", self.get_note_by_aspn, methods=["GET"], response_model=NoteApiResponse)
        self.router.add_api_route("/a", self.get_note_by_midi, methods=["GET"], response_model=NoteApiResponse)

    def get_note_by_aspn(self, note: str = Query(..., description="Note in ASPN format (e.g., C4, A#3)")) -> NoteApiResponse:
        self.logger.info(f"{__name__} endpoint accessed with note: {note}")
        result = note_service().get_note_by_aspn(note)
        self.logger.info(f"{__name__} result: {result}")
        return self.build_success_response(result, f"Note {note} retrieved successfully")

    def get_note_by_midi(self, midi: int = Query(..., description="MIDI value (0-127)")) -> NoteApiResponse:
        self.logger.info(f"{__name__} endpoint accessed with midi: {midi}")
        result = note_service().get_note_by_midi(midi)
        self.logger.info(f"{__name__} result: {result}")
        return self.build_success_response(result, f"Note for MIDI {midi} retrieved successfully")


note_controller = NoteController()
router = note_controller.router


