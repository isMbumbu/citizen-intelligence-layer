from app.models.service_state import ServiceState


def test_service_state_builds_uuid_and_aware_timestamps() -> None:
    """The initial SQLModel model uses safe persistence defaults."""
    state = ServiceState(key="migration", value="verified")

    assert state.id
    assert state.created_at.tzinfo is not None
    assert state.updated_at.tzinfo is not None
