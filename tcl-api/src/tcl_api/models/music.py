from enum import Enum

from pydantic import BaseModel

class Note(BaseModel):
    note_name: str
    octave: int
    aspn: str  # e.g., 'C4', 'G#3'
    modifier: int # e.g., -1 for flat, 0 for natural, +1 for sharp

class Chord(BaseModel):
    notes: list[Note]
    name: str

class Key(BaseModel):
    root: Note
    quality: str # e.g., 'major', 'minor'

class Step(BaseModel):
    size: int # in semitones
    shorthand: str # e.g., 'M2' for major second
    formal_name: str # e.g., 'Major Second'

class Scale(BaseModel):
    root: Note
    step_pattern: list[str] # e.g., ['W', 'W', 'H', 'W', 'W', 'W', 'H']

class Interval(BaseModel):
    root: Note
    target: Note
    semitone_distance: int # can be deduced from root and target

class AccidentalStrRepr(str, Enum):
    DOUBLE_FLAT = "bb"
    FLAT = "b"
    NATURAL = ""
    SHARP = "#"
    DOUBLE_SHARP = "##"
