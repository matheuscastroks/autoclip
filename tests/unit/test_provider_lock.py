import threading
import pytest
from engine.pipeline.provider_lock import provider_slot
from engine.contracts import PipelineError

def test_provider_slots_are_exclusive_and_released(tmp_path):
    entered=threading.Event()
    def second():
        with provider_slot(tmp_path):entered.set()
    with provider_slot(tmp_path):
        worker=threading.Thread(target=second);worker.start()
        assert not entered.wait(.3)
    assert entered.wait(2);worker.join(2)

def test_waiting_provider_slot_is_cancellable(tmp_path):
    with provider_slot(tmp_path):
        with pytest.raises(PipelineError) as e:
            with provider_slot(tmp_path,cancelled=lambda:True):pass
        assert e.value.code=='CANCELLED'
