from pydantic import BaseModel


class Note(BaseModel):
    aspn: str # e.g., "C4, A#3"
    midi: int # e.g., 60, 61
    octave: int
    root: str # e.g., "C, E, F, B"
    modifier: Modifier

class Modifier(BaseModel):
    type: str # e.g., "sharp, flat, natural"
    symbol: str # e.g., "#, b, ♮"
    modifier: int # e.g., 1, -1, 0

class Scale(BaseModel):
    content: str = "This is a sample scale."

class Mode(BaseModel):
    steps: list[Step] # e.g., "Step(M2),M2 m2 M2 M2 M2 m2"
    name: str # e.g., "Ionian, Major, minor, pentatonic."

class Chord(BaseModel):
    notes: list[Note] = []
    name: str # e.g., "Major, minor, diminished, augmented, also used for intervals Perfect Fifth with root and fifth"
    steps: list[Step] = [] # steps from root to build chord

class Step(BaseModel):
    shorthand: str # e.g., "M2, m2, P4, P5"
    qualified_name: str # e.g., "Major Second, minor second, Perfect Fourth, Perfect Fifth"
    size: int # in semitones
