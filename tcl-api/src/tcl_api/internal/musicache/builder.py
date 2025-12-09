from typing import Dict, Set
from .cache import MusicCache


def build_music_cache() -> MusicCache:
    midi_to_note = _build_midi_to_note()
    note_to_midi = {v: k for k, v in midi_to_note.items()}
    frequencies = _build_frequencies()
    note_names = set(midi_to_note.values())
    
    return MusicCache(
        midi_to_note=midi_to_note,
        note_to_midi=note_to_midi,
        frequencies=frequencies,
        note_names=note_names,
    )


def _build_midi_to_note() -> Dict[int, str]:
    """Build MIDI value to note name mapping (C-1 to G9)."""
    note_sequence = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    midi_to_note = {}
    
    for midi_value in range(0, 128):
        octave = (midi_value // 12) - 1
        note_index = midi_value % 12
        note_name = f"{note_sequence[note_index]}{octave}"
        midi_to_note[midi_value] = note_name
    
    return midi_to_note


def _build_frequencies() -> Dict[int, float]:
    a4_midi = 69
    a4_freq = 440.0
    frequencies = {}
    
    for midi_value in range(0, 128):
        cents_from_a4 = (midi_value - a4_midi) * 100
        frequency = a4_freq * (2.0 ** (cents_from_a4 / 1200.0))
        frequencies[midi_value] = round(frequency, 2)
    
    return frequencies
