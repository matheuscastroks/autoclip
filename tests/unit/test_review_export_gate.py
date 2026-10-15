import json
from uuid import uuid4

import pytest

from engine.api.reviews import list_revisions
from engine.contracts import (
    CaptionArtifact,
    Candidate,
    EDLArtifact,
    EditorialChecks,
    EditorialFlags,
    ExportValidation,
    PipelineError,
    ProjectRun,
    RenderArtifact,
    Source,
    Span,
)
from engine.editorial.review import record_review, review_fingerprint
from engine.pipeline.artifacts import atomic_json, file_hash
from engine.pipeline.runner import export_approved


def revision_project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    source_file = root / 'source.mp4'
    source_file.write_bytes(b'source fixture')
    source = Source(local_path=source_file, sha256=file_hash(source_file))
    revision_id = uuid4()
    transcript_id = uuid4()
    folder = root / 'revisions' / str(revision_id)
    folder.mkdir(parents=True)
    render_path = folder / 'preview.mp4'
    render_path.write_bytes(b'preview fixture')
    ass_path = folder / 'captions.ass'
    srt_path = folder / 'captions.srt'
    ass_path.write_text('ASS fixture', encoding='utf-8')
    srt_path.write_text('SRT fixture', encoding='utf-8')
    atomic_json(root / 'source.json', source)
    atomic_json(root / 'project.json', ProjectRun(source=source, status='needs_review', revisions=[{'revision_id': str(revision_id)}]))
    atomic_json(folder / 'edl.json', EDLArtifact(revision_id=revision_id, source_id=source.id, transcript_id=transcript_id, spans=[Span(source_start_us=0, source_end_us=1_000_000, output_start_us=0, output_end_us=1_000_000)], protected_word_ids=[], duration_us=1_000_000))
    atomic_json(folder / 'candidate.json', Candidate(topic_id='fixture', start_word_id='w1', end_word_id='w1', evidence_word_ids=['w1'], rationale='Test only', editorial=EditorialFlags(completeness='yes', standalone_context='yes', qualification_preserved='yes')))
    atomic_json(folder / 'captions.json', CaptionArtifact(transcript_id=transcript_id, edl_revision_id=revision_id, revision_id=uuid4(), words=[], ass_path=ass_path, srt_path=srt_path, font='Fixture'))
    atomic_json(folder / 'render.json', RenderArtifact(revision_id=revision_id, path=render_path, sha256=file_hash(render_path), size_bytes=render_path.stat().st_size))
    atomic_json(folder / 'qa.json', ExportValidation(revision_id=revision_id, technical_pass=True, checks={}))
    return root, folder, revision_id


def save_decision(root, folder, revision_id, decision, content_hash=None):
    checks = EditorialChecks(completeness=True, context=True, qualifications=True, words_and_boundaries=True, audiovisual=True)
    atomic_json(folder / 'review.json', record_review(revision_id, decision, checks, 'Test only', content_hash or review_fingerprint(root, revision_id)))


def test_technical_pass_without_review_is_not_exportable(tmp_path):
    root, _, revision_id = revision_project(tmp_path)
    assert list_revisions(root)[0]['review_status'] == 'needs_review'
    with pytest.raises(PipelineError) as error:
        export_approved(root)
    assert error.value.code == 'NO_APPROVED_CLIPS'
    assert not (root / 'exports' / str(revision_id)).exists()


def test_rejected_revision_is_not_exportable(tmp_path):
    root, folder, revision_id = revision_project(tmp_path)
    save_decision(root, folder, revision_id, 'rejected')
    assert list_revisions(root)[0]['review_status'] == 'rejected'
    with pytest.raises(PipelineError) as error:
        export_approved(root)
    assert error.value.code == 'NO_APPROVED_CLIPS'


def test_technically_invalid_revision_is_skipped_by_automatic_export(tmp_path):
    root, folder, revision_id = revision_project(tmp_path)
    atomic_json(folder / 'qa.json', ExportValidation(revision_id=revision_id, technical_pass=False, checks={}))
    assert list_revisions(root)[0]['review_status'] == 'invalid'
    with pytest.raises(PipelineError) as error:
        export_approved(root)
    assert error.value.code == 'NO_APPROVED_CLIPS'


def test_approved_revision_exports_decision_and_stale_approval_does_not(tmp_path):
    root, folder, revision_id = revision_project(tmp_path)
    save_decision(root, folder, revision_id, 'approved')
    assert list_revisions(root)[0]['review_status'] == 'approved'
    assert list_revisions(root)[0]['exported'] is False
    package = export_approved(root)[0]
    assert json.loads((__import__('pathlib').Path(package) / 'metadata.json').read_text(encoding='utf-8'))['review']['decision'] == 'approved'
    assert list_revisions(root)[0]['exported'] is True
    (folder / 'captions.ass').write_text('Changed captions', encoding='utf-8')
    assert list_revisions(root)[0]['review_status'] == 'stale_review'
    assert list_revisions(root)[0]['exported'] is False
    with pytest.raises(PipelineError) as error:
        export_approved(root, [str(revision_id)])
    assert error.value.code == 'REVIEW_REQUIRED'
