import uuid
from engine.contracts import TranscriptArtifact, Word, Segment, PipelineError
from engine.contracts.api import SegmentUpdate

def apply_transcript_updates(transcript: TranscriptArtifact, updates: list[SegmentUpdate]) -> TranscriptArtifact:
    """Applies textual updates to segments while strictly preserving audio timeline intervals."""
    if not updates:
        return transcript

    update_map = {u.id: u.text.strip() for u in updates}
    existing_segment_ids = {s.id for s in transcript.segments}
    unknown_ids = set(update_map) - existing_segment_ids
    if unknown_ids:
        raise PipelineError('SEGMENT_NOT_FOUND', 'transcript_editor', f'Unknown segment ID(s): {", ".join(sorted(unknown_ids))}')

    words_by_id = {w.id: w for w in transcript.words}
    
    # We will build updated segments and an updated word list
    updated_segments: list[Segment] = []
    
    # Map to track replacements: segment_id -> list[Word]
    segment_new_words: dict[str, list[Word]] = {}

    for seg in transcript.segments:
        if seg.id not in update_map:
            updated_segments.append(seg)
            continue

        new_text = update_map[seg.id]
        if not new_text:
            raise PipelineError('EMPTY_SEGMENT_TEXT', 'transcript_editor', f'Segment {seg.id} text cannot be empty.')

        new_tokens = new_text.split()
        old_words = [words_by_id[wid] for wid in seg.word_ids if wid in words_by_id]
        
        if len(new_tokens) == len(old_words) and len(old_words) > 0:
            # 1:1 replacement: maintain exact word timestamps and IDs
            new_words = []
            for token, old_w in zip(new_tokens, old_words):
                new_words.append(Word(
                    id=old_w.id,
                    text=token,
                    start_us=old_w.start_us,
                    end_us=old_w.end_us,
                    probability=old_w.probability,
                    speaker_id=old_w.speaker_id,
                ))
            segment_new_words[seg.id] = new_words
            updated_segments.append(Segment(
                id=seg.id,
                start_us=seg.start_us,
                end_us=seg.end_us,
                text=new_text,
                word_ids=[w.id for w in new_words],
            ))
        else:
            # Word count changed: redistribute duration across new tokens proportionally
            seg_duration = max(1, seg.end_us - seg.start_us)
            num_tokens = len(new_tokens)
            total_chars = max(num_tokens, sum(len(t) for t in new_tokens))
            
            new_words = []
            current_start = seg.start_us
            
            for i, token in enumerate(new_tokens):
                # Reuse old word IDs where possible, generate deterministic/unique IDs for overflow
                if i < len(old_words):
                    word_id = old_words[i].id
                    speaker_id = old_words[i].speaker_id
                    prob = old_words[i].probability
                else:
                    word_id = f'{seg.id}_w{i}_{uuid.uuid4().hex[:6]}'
                    speaker_id = old_words[-1].speaker_id if old_words else None
                    prob = None
                
                # Proportion of duration based on character length
                if i == num_tokens - 1:
                    token_end = seg.end_us
                else:
                    char_weight = len(token) / total_chars
                    duration_part = max(1, int(round(seg_duration * char_weight)))
                    # Ensure we leave at least 1 us for each subsequent word
                    remaining_tokens = num_tokens - 1 - i
                    max_allowed_end = seg.end_us - remaining_tokens
                    token_end = min(max_allowed_end, max(current_start + 1, current_start + duration_part))

                new_words.append(Word(
                    id=word_id,
                    text=token,
                    start_us=current_start,
                    end_us=token_end,
                    probability=prob,
                    speaker_id=speaker_id,
                ))
                current_start = token_end

            segment_new_words[seg.id] = new_words
            updated_segments.append(Segment(
                id=seg.id,
                start_us=seg.start_us,
                end_us=seg.end_us,
                text=new_text,
                word_ids=[w.id for w in new_words],
            ))

    # Reconstruct the complete word list preserving sequence
    final_words: list[Word] = []
    # Set of word IDs covered by segmented replacements
    all_replaced_old_wids = set()
    for seg in transcript.segments:
        if seg.id in segment_new_words:
            all_replaced_old_wids.update(seg.word_ids)

    # For words outside edited segments, keep them. For edited segments, inject new words in order.
    inserted_segment_ids = set()
    for seg in transcript.segments:
        if seg.id in segment_new_words:
            if seg.id not in inserted_segment_ids:
                final_words.extend(segment_new_words[seg.id])
                inserted_segment_ids.add(seg.id)
        else:
            for wid in seg.word_ids:
                if wid in words_by_id:
                    final_words.append(words_by_id[wid])

    # In case there were unsegmented words (if any)
    segmented_wids = {w.id for w in final_words} | all_replaced_old_wids
    for w in transcript.words:
        if w.id not in segmented_wids:
            final_words.append(w)

    final_words.sort(key=lambda w: (w.start_us, w.end_us))

    has_text_changes = any(
        seg.id in update_map and update_map[seg.id] != seg.text
        for seg in transcript.segments
    )
    new_transcript_id = uuid.uuid4() if has_text_changes else transcript.transcript_id

    return TranscriptArtifact(
        schema_version=transcript.schema_version,
        transcript_id=new_transcript_id,
        source_id=transcript.source_id,
        source_sha256=transcript.source_sha256,
        language=transcript.language,
        model=transcript.model,
        words=final_words,
        segments=updated_segments,
        warnings=list(transcript.warnings),
    )
