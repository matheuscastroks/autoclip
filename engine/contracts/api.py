"""Response contracts shared by the HTTP API and generated TypeScript types."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import Source, RenderProfile

RevisionReviewStatus = Literal['invalid', 'needs_review', 'stale_review', 'approved', 'rejected']
ArtifactState = Literal['available', 'not_generated', 'invalid', 'unavailable', 'stale']
JobStatus = Literal['pending', 'running', 'cancelling', 'completed', 'failed', 'cancelled', 'interrupted', 'rejected']
ProjectStatus = Literal['pending_import', 'imported', 'processing', 'transcribed', 'analyzed', 'needs_review', 'no_candidates', 'completed', 'failed', 'cancelled', 'interrupted', 'manual_preview']
AnalysisState = Literal['not_started', 'running', 'partial', 'completed', 'failed', 'cancelled', 'interrupted', 'invalid', 'unavailable', 'stale']


class Response(BaseModel):
    # Preserve compatible metadata from older workers while validating known fields.
    model_config = ConfigDict(extra='allow', allow_inf_nan=False)


class Error(Response):
    code: str
    message: str


class ArtifactDiagnostic(Response):
    state: ArtifactState
    message: str | None = None


class ProjectSummary(Response):
    proposed: int | None = None
    selected: int | None = None
    generated: int = 0
    stage: str | None = None


class Project(Response):
    id: str
    name: str
    title: str
    path: str
    status: ProjectStatus
    duration_us: int
    has_transcript: bool
    has_analysis: bool
    word_count: int
    is_manual: bool
    revisions: list[dict[str, str]]
    warnings: list[str]
    created_at: str
    updated_at: float
    source: Source | None
    error: Error | None
    summary: ProjectSummary | None = None
    artifacts: dict[str, ArtifactDiagnostic] = Field(default_factory=dict)


class AnalysisTopic(Response):
    id: str
    label: str
    summary: str
    evidence_word_ids: list[str]


class EventCandidate(Response):
    id: str
    title_suggestion: str
    rationale: str
    start_word_id: str
    end_word_id: str
    start_us: int | None = None
    end_us: int | None = None
    editorial: dict[str, str] | None = None


class Usage(Response):
    thoughts_token_count: int | None = None
    candidates_token_count: int | None = None


class AnalysisEvent(Response):
    id: str = ''
    at: str = ''
    kind: str = ''
    message: str = ''
    window_id: str | None = None
    window_index: int | None = None
    windows: int | None = None
    attempt: int | None = None
    model: str | None = None
    source_start_us: int | None = None
    source_end_us: int | None = None
    topics: list[AnalysisTopic] | None = None
    candidates: list[EventCandidate] | None = None
    usage: Usage | None = None


class GenerationItem(Response):
    candidate_id: str
    title: str = 'Trecho'
    state: Literal['pending', 'running', 'ready', 'failed', 'cancelled']
    phase: str = 'waiting'
    processed_us: int = 0
    total_us: int | None = None
    revision_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_stage: str | None = None
    error_type: str | None = None
    reused: bool | None = None


class JobProgress(Response):
    stage: str = ''
    steps: dict[str, str] = Field(default_factory=dict)
    phase: str | None = None
    items: list[GenerationItem] | None = None
    completed_items: int | None = None
    total_items: int | None = None
    processed_us: int | None = None
    total_us: int | None = None
    activity_at: str | None = None


class Job(Response):
    id: str
    project_id: str
    status: JobStatus
    operation: Literal['', 'prepare', 'import', 'transcribe', 'analyze', 'preview', 'render_final', 'render', 'export'] = ''
    created_at: str = ''
    requests_used: int = 0
    request_limit: int | None = None
    request_mode: Literal['automatic', 'manual'] | None = None
    events: list[AnalysisEvent] = Field(default_factory=list)
    queue_position: int | None = None
    queue_reason: str | None = None
    ignored_ready: int | None = None
    ignored_queued: int | None = None
    enqueued_items: int | None = None
    stage: str | None = None
    progress: JobProgress | None = None
    error: Error | None = None
    exports: list[str] | None = None


class CaptionWord(Response):
    display_text: str
    start_us: int
    end_us: int


class PauseRemoval(Response):
    source_start_us: int
    source_end_us: int
    reason: str


class OutputVersion(Response):
    state: Literal['available', 'invalid', 'not_generated']
    asset: str | None = None
    profile: RenderProfile | None = None
    sha256: str | None = None
    duration_us: int | None = None
    message: str | None = None


class Revision(Response):
    revision_id: str
    title: str
    technical_pass: bool
    review_status: RevisionReviewStatus
    warnings: list[str]
    candidate_id: str | None = None
    exported: bool = False
    rationale: str | None = None
    description: str | None = None
    opening_text: str | None = None
    opening_duration_us: int | None = None
    duration_us: int | None = None
    start_us: int | None = None
    end_us: int | None = None
    caption_words: list[CaptionWord] | None = None
    content_hash: str | None = None
    notes: str | None = None
    removed_silence_us: int | None = None
    pause_removals: list[PauseRemoval] | None = None
    preview: OutputVersion | None = None
    final_state: Literal['available', 'invalid', 'not_generated'] | None = None
    can_render_final: bool | None = None
    analysis_hash: str | None = None
    plan_hash: str | None = None


class Proposal(Response):
    candidate_id: str
    topic_ids: list[str]
    group_id: str
    title: str
    rationale: str
    start_us: int
    end_us: int
    duration_us: int
    start_word_id: str
    end_word_id: str
    evidence_word_ids: list[str]
    editorial: dict[str, str]
    warnings: list[str]
    eligible: bool
    reasons: list[str]
    text: str
    context_before: str
    context_after: str
    opening_text: str = ''
    description: str = ''


class TopicGroup(Response):
    id: str
    label: str
    topic_ids: list[str]
    summaries: list[str]
    evidence_word_ids: list[str]


class AnalysisView(Response):
    schema_version: Literal['1.0'] = '1.0'
    state: AnalysisState
    job_id: str | None
    analysis_hash: str | None
    model: str | None
    completed_windows: int
    total_windows: int
    topic_groups: list[TopicGroup]
    proposals: list[Proposal]
    diagnostic: str | None = None


class CreatedProject(Response):
    project: Project
    job: Job


API_MODELS = (Project, Job, Revision, Proposal, AnalysisView, GenerationItem, AnalysisEvent)
