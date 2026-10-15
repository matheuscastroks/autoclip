"""Shared preparation and independently cached preview/final outputs."""
from pathlib import Path
from uuid import UUID, uuid4

from engine.contracts import (
    Candidate, CaptionArtifact, CropArtifact, EDLArtifact, ExportConfig,
    ExportValidation, PipelineError, PreparationArtifact, PreviewArtifact,
    RenderArtifact, RenderProfile, Source,
)
from engine.pipeline.artifacts import atomic_json, file_hash, object_hash
from engine.pipeline.cancellation import run_process
from engine.pipeline.fingerprints import stage_dependencies, tool_fingerprint
from engine.pipeline.manifest import StageCache
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_preview, verify_render


def revision_path(root: Path, revision_id) -> Path:
    return Path(root).resolve() / 'revisions' / str(UUID(str(revision_id)))


def preparation_files(root, folder):
    files = {name: file_hash(folder / name) for name in ('edl.json', 'candidate.json', 'captions.json', 'crop.json')}
    captions = CaptionArtifact.model_validate_json((folder / 'captions.json').read_bytes())
    for field in ('ass_path', 'srt_path'):
        path = getattr(captions, field).resolve()
        if not path.is_relative_to(Path(root).resolve()):
            raise PipelineError('UNSAFE_PATH', 'prepare', 'Caption outside project.')
        files[field] = file_hash(path)
    font = Path(captions.font)
    if font.is_file():
        files['font'] = file_hash(font)
    return files


def save_preparation(root, folder, *, analysis_hash, plan_hash):
    source = Source.model_validate_json((root / 'source.json').read_bytes())
    candidate = Candidate.model_validate_json((folder / 'candidate.json').read_bytes())
    values = dict(revision_id=UUID(folder.name), candidate_id=candidate.id,
                  analysis_hash=analysis_hash, source_hash=source.sha256,
                  plan_hash=plan_hash, files=preparation_files(root, folder))
    prepared = PreparationArtifact(**values, fingerprint=object_hash(values))
    atomic_json(folder / 'prepared.json', prepared)
    return prepared


def load_preparation(root, revision_id):
    root = Path(root).resolve()
    folder = revision_path(root, revision_id)
    try:
        if (folder / 'deleted.json').exists():
            raise ValueError('Revision is in trash')
        prepared = PreparationArtifact.model_validate_json((folder / 'prepared.json').read_bytes())
        values = prepared.model_dump(exclude={'schema_version', 'fingerprint'})
        # UUIDs serialize identically in object_hash's canonical encoder.
        if prepared.revision_id != UUID(str(revision_id)) or object_hash(values) != prepared.fingerprint:
            raise ValueError('Preparation identity changed')
        if preparation_files(root, folder) != prepared.files:
            raise ValueError('Shared artifacts changed')
        source = Source.model_validate_json((root / 'source.json').read_bytes())
        if source.sha256 != prepared.source_hash or file_hash(source.local_path) != source.sha256:
            raise ValueError('Source changed')
        edl = EDLArtifact.model_validate_json((folder / 'edl.json').read_bytes())
        caps = CaptionArtifact.model_validate_json((folder / 'captions.json').read_bytes())
        crop = CropArtifact.model_validate_json((folder / 'crop.json').read_bytes())
        candidate = Candidate.model_validate_json((folder / 'candidate.json').read_bytes())
        if candidate.id != prepared.candidate_id or edl.revision_id != prepared.revision_id or edl.source_id != source.id:
            raise ValueError('Revision provenance mismatch')
        return folder, prepared, source, edl, caps, crop
    except (OSError, ValueError) as exc:
        raise PipelineError('PREPARATION_CHANGED', 'prepare', 'Shared preparation unavailable or changed; generate a new preview.') from exc


def render_output(root: Path, revision_id, profile: RenderProfile, ffmpeg: Path, ffprobe: Path,
                  *, cancelled=lambda: False, progress=None):
    def check():
        if cancelled():
            raise PipelineError('CANCELLED', profile.name, 'Cancellation requested.')

    check()
    root = Path(root).resolve()
    folder, prepared, source, edl, caps, crop = load_preparation(root, revision_id)
    tools = {'ffmpeg': tool_fingerprint(ffmpeg), 'ffprobe': tool_fingerprint(ffprobe)}
    inputs = {'prepared': prepared.fingerprint, 'profile': profile,
              'ffmpeg': tools['ffmpeg'], 'runtime': stage_dependencies('render')}
    output_key = object_hash(inputs)
    config = ExportConfig(output_root=root / 'outputs' / profile.name / output_key, profile=profile)
    cache = StageCache(root)

    def produce():
        check()
        existing = config.output_root / f'{edl.revision_id}.mp4'
        if existing.exists():
            existing.replace(existing.with_suffix('.corrupt-' + uuid4().hex))
        return FFmpegRenderer(ffmpeg, run=lambda cmd, **kw: run_process(cmd, cancelled=cancelled, **kw),
                              progress=progress).render(source, edl, crop, caps, config)

    rendered = cache.run('output_' + profile.name, inputs, produce, RenderArtifact)
    check()
    if progress:
        progress(edl.duration_us, edl.duration_us, phase='verify')
    validation_inputs = {'render': rendered, 'edl': edl, 'tools': tools,
                         'runtime': stage_dependencies('verify')}
    if profile.name == 'preview':
        checks = verify_preview(rendered, source, edl, ffprobe, profile, cancelled)
        if not all(checks.values()):
            raise PipelineError('PREVIEW_INVALID', 'verify', 'Preview stream validation failed.')
        result = PreviewArtifact(revision_id=edl.revision_id, prepared_hash=prepared.fingerprint,
                                 render=rendered, profile=profile, duration_us=edl.duration_us, checks=checks)
        check()
        atomic_json(folder / 'preview.json', result)
    else:
        qa = cache.run('output_verify', validation_inputs,
                       lambda: verify_render(rendered, source, edl, ffprobe, ffmpeg, cancelled), ExportValidation)
        if not qa.technical_pass:
            raise PipelineError('EXPORT_INVALID', 'verify', 'Final technical QA failed.')
        check()
        # Do not replace a valid final or its review until new full QA succeeds.
        atomic_json(folder / 'render.json', rendered)
        atomic_json(folder / 'qa.json', qa)
        result = rendered
    return result, ('output_' + profile.name) in cache.reused
