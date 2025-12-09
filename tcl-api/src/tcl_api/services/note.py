from typing import Optional
from tcl_api.config import get_logger
from tcl_api.internal.musicache import MusicCache, get_cache
from tcl_api.models.music import Note


class NoteService:
    def __init__(self, music_cache: MusicCache):
        self.logger = get_logger("services.note")
        self.music_cache = music_cache

    def get_note_by_aspn(self, note_name: str) -> Note:
        self.logger.debug(f"Getting note information for: {note_name}")

        # Validate the note using the music cache
        if not self.music_cache.is_valid_note(note_name):
            self.logger.warning(f"Invalid note name provided: {note_name}")
            raise ValueError(f"Invalid note name: {note_name}")

        # Get MIDI value and frequency for the note
        midi_value = self.music_cache.get_midi_value(note_name)
        frequency = None
        if midi_value:
            frequency = self.music_cache.get_frequency(midi_value)

        response = Note(
            content=f"Note: {note_name}, MIDI: {midi_value}, Frequency: {frequency}Hz"
        )
        self.logger.info(f"Note information retrieved successfully for: {note_name}")
        return response

    def get_note_by_midi(self, midi_value: int) -> Note:
        self.logger.debug(f"Getting note information for MIDI value: {midi_value}")

        # Get note name and frequency for the MIDI value
        note_name = self.music_cache.get_note_name(midi_value)
        frequency = self.music_cache.get_frequency(midi_value)

        if not note_name:
            self.logger.warning(f"Invalid MIDI value provided: {midi_value}")
            raise ValueError(f"Invalid MIDI value: {midi_value}")

        response = Note(
            content=f"Note: {note_name}, MIDI: {midi_value}, Frequency: {frequency}Hz"
        )
        self.logger.info(f"Note information retrieved successfully for MIDI: {midi_value}")
        return response


# Module-level lazy initialization
_note_service_instance: Optional[NoteService] = None


def get_note_service() -> NoteService:
    global _note_service_instance
    if _note_service_instance is None:
        _note_service_instance = NoteService(get_cache())
    return _note_service_instance

note_service = get_note_service
