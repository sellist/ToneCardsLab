from typing import Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class MusicCache:
    midi_to_note: Dict[int, str]
    note_to_midi: Dict[str, int]
    frequencies: Dict[int, float]
    note_names: Set[str]

    def __post_init__(self):
        object.__setattr__(self, '_frozen', True)

    def __setattr__(self, name, value):
        if getattr(self, '_frozen', False):
            raise AttributeError(f"Cannot modify frozen cache attribute: {name}")
        super().__setattr__(name, value)

    def get_note_name(self, midi_value: int) -> Optional[str]:
        return self.midi_to_note.get(midi_value)

    def get_midi_value(self, note_name: str) -> Optional[int]:
        return self.note_to_midi.get(note_name)

    def get_frequency(self, midi_value: int) -> Optional[float]:
        return self.frequencies.get(midi_value)

    def is_valid_note(self, note_name: str) -> bool:
        return note_name in self.note_names


_cache: Optional[MusicCache] = None


def get_cache() -> MusicCache:
    if _cache is None:
        raise RuntimeError("Music cache not initialized. Call set_cache() at startup.")
    return _cache


def set_cache(cache: MusicCache) -> None:
    global _cache
    if _cache is not None:
        raise RuntimeError("Music cache already initialized")
    _cache = cache

