"""Tests for bot states."""

from aiogram.fsm.state import State, StatesGroup

from bot.states.profile import CreateProfileState, UpdateProfileState


class TestCreateProfileState:
    """Tests for create profile FSM states."""

    def test_create_profile_states_exist(self):
        """Test that all required states exist."""
        assert hasattr(CreateProfileState, "name")
        assert hasattr(CreateProfileState, "age")
        assert hasattr(CreateProfileState, "city")
        assert hasattr(CreateProfileState, "bio")
        assert hasattr(CreateProfileState, "interests")
        assert hasattr(CreateProfileState, "photo")

    def test_create_profile_states_are_state_objects(self):
        """Test that states are State objects."""
        assert isinstance(CreateProfileState.name, State)
        assert isinstance(CreateProfileState.age, State)
        assert isinstance(CreateProfileState.city, State)

    def test_create_profile_state_group(self):
        """Test that CreateProfileState is a StatesGroup."""
        assert issubclass(CreateProfileState, StatesGroup)


class TestUpdateProfileState:
    """Tests for update profile FSM states."""

    def test_update_profile_states_exist(self):
        """Test that value state exists."""
        assert hasattr(UpdateProfileState, "value")

    def test_update_profile_state_is_state_object(self):
        """Test that value state is a State object."""
        assert isinstance(UpdateProfileState.value, State)

    def test_update_profile_state_group(self):
        """Test that UpdateProfileState is a StatesGroup."""
        assert issubclass(UpdateProfileState, StatesGroup)
