import pytest
from uuid import uuid4
def test_no_approval_for_uncertain_editorial_check():
    from engine.editorial.review import record_review
    from engine.contracts import EditorialChecks
    checks=EditorialChecks(completeness=True,context=True,qualifications=False,words_and_boundaries=True,audiovisual=True)
    with pytest.raises(ValueError): record_review(uuid4(),'approved',checks,'not verified')
    assert record_review(uuid4(),'rejected',checks,'missing qualification').author_kind=='human'
