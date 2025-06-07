import pytest
from tools.data_processing.can_field_definitions import CanProcessingField

# Test data (moved from original file)
can_id_20b_example = 888888883

@pytest.fixture
def candidate_with_can_id():
    return {"can_id": can_id_20b_example, "msg_type": "SOME_TYPE", "data": {"value": 999}}

@pytest.fixture
def candidate_without_can_id():
    return {"msg_type": "SOME_TYPE", "data": {"value": 999}}

@pytest.fixture
def correct_candidate():
    return {"msg_type": "SENSOR_ANALOG", "data": {
        "sensor_id": "SENSOR_PRESSURE_OX", "value": 100, "req_state": "OPEN"}}

@pytest.fixture
def missing_value_candidate():
    return {"msg_type": "SENSOR_ANALOG",
                               "data": {"sensor_id": "SENSOR_PRESSURE_OX", "req_state": "OPEN"}}

@pytest.fixture
def false_candidate():
    return {"msg_type": "SENSOR_ANALOG",
                       "data": {"sensor_id": "NOT_THE_ONE", "value": 100, "req_state": "OPEN"}}

@pytest.fixture
def missing_data_candidate():
    return {"msg_type": "SENSOR_ANALOG"}

@pytest.fixture
def correct_matching_pattern():
    return {"msg_type": "SENSOR_ANALOG", "data.sensor_id": "SENSOR_PRESSURE_OX"}

@pytest.fixture
def incorrect_matching_pattern():
    return {"msg_type": "SENSOR_ANALOG",
                                  "data.sensor_id": "SENSOR_PRESSURE_FUEL"}

@pytest.fixture
def inexistant_matching_pattern():
    return {"msg_type": "SENSOR_ANALOG",
                                   "mangoes.pears": "SENSOR_PRESSURE_OX"}

@pytest.fixture
def correct_reading_signature():
    return "data.value"

@pytest.fixture
def incorrect_reading_signature():
    return "data.req_state"

@pytest.fixture
def inexistant_reading_signature():
    return "data.mangoes"

def test_matching_and_reading_signature(correct_candidate, missing_value_candidate, false_candidate, missing_data_candidate,
                                        correct_matching_pattern, incorrect_matching_pattern, inexistant_matching_pattern,
                                        correct_reading_signature, incorrect_reading_signature, inexistant_reading_signature):
    cmatch_cread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=correct_reading_signature)
    cmatch_iread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=incorrect_reading_signature)
    cmatch_ixread = CanProcessingField(
        "ox tank", correct_matching_pattern, reading_signature=inexistant_reading_signature)
    imatch_cread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=correct_reading_signature)
    imatch_iread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=incorrect_reading_signature)
    imatch_ixread = CanProcessingField(
        "ox tank", incorrect_matching_pattern, reading_signature=inexistant_reading_signature)
    ixmatch_cread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=correct_reading_signature)
    ixmatch_iread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=incorrect_reading_signature)
    ixmatch_ixread = CanProcessingField(
        "ox tank", inexistant_matching_pattern, reading_signature=inexistant_reading_signature)

    assert cmatch_cread.match(correct_candidate)
    assert cmatch_iread.match(correct_candidate)
    assert cmatch_ixread.match(correct_candidate)
    assert not imatch_cread.match(correct_candidate)
    assert not imatch_iread.match(correct_candidate)
    assert not imatch_ixread.match(correct_candidate)
    assert not ixmatch_cread.match(correct_candidate)
    assert not ixmatch_iread.match(correct_candidate)
    assert not ixmatch_ixread.match(correct_candidate)

    assert cmatch_cread.read(correct_candidate) == 100
    assert cmatch_iread.read(correct_candidate) is None
    assert cmatch_ixread.read(correct_candidate) is None
    assert imatch_cread.read(correct_candidate) is None
    assert imatch_iread.read(correct_candidate) is None
    assert imatch_ixread.read(correct_candidate) is None
    assert ixmatch_cread.read(correct_candidate) is None
    assert ixmatch_iread.read(correct_candidate) is None
    assert ixmatch_ixread.read(correct_candidate) is None

    assert not cmatch_cread.match(false_candidate)
    assert not imatch_cread.match(false_candidate)
    assert not ixmatch_cread.match(false_candidate)

    assert cmatch_cread.read(missing_value_candidate) is None

    assert not cmatch_cread.match(missing_data_candidate)
