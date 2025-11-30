import pytest
from tcl_api.controllers import note_controller


def test_health_check_passes_model_and_generates_metadata(monkeypatch):
    expected_model = {"pitch": "C4", "octave": 4}

    class FakeNoteService:
        def get_note_from_aspn(self, aspn: str):
            assert aspn == "aspn-1"
            return expected_model

    fake_service = FakeNoteService()

    captured = {}

    class MockResponseBuilder:
        def __init__(self, payload):
            captured["payload"] = payload

        def build(self):
            return {"data": captured["payload"], "meta": {"generated_by": "MockResponseBuilder"}}

    monkeypatch.setattr(note_controller, "ResponseBuilder", MockResponseBuilder)

    result = note_controller.health_check("aspn-1", service=fake_service)

    assert captured["payload"] == expected_model

    assert result["data"] == expected_model
    assert result["meta"] == {"generated_by": "MockResponseBuilder"}
