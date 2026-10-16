import re
import pytest
from pydantic import ValidationError

from test_gemini import transcript, payload
from engine.contracts import Source, Candidate, CaptionConfig, CaptionRevision, CaptionArtifact
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.render.presets import (
    PRESET_CATALOG_VERSION,
    VIDEO_STYLE_PRESETS,
    get_preset,
    list_presets,
    resolve_preset_id,
    validate_known_preset_id,
)


def test_preset_catalog_exposes_four_fixed_versioned_styles():
    assert PRESET_CATALOG_VERSION == 1
    assert tuple(VIDEO_STYLE_PRESETS.keys()) == (
        'karaoke_yellow',
        'editorial_sober',
        'documentary',
        'impact',
    )
    listed = list_presets()
    assert [item['id'] for item in listed] == [
        'karaoke_yellow',
        'editorial_sober',
        'documentary',
        'impact',
    ]
    assert all(item['version'] == PRESET_CATALOG_VERSION for item in listed)


@pytest.mark.parametrize('invalid', ['', 'custom', 'neon', 'karaoke', 'bold-uppercase-v1', 'unknown'])
def test_strict_preset_validation_rejects_unknown_or_legacy_ids(invalid):
    with pytest.raises(ValueError):
        validate_known_preset_id(invalid)


def test_legacy_style_ids_resolve_to_karaoke_yellow_for_stored_artifacts():
    assert resolve_preset_id(None) == 'karaoke_yellow'
    assert resolve_preset_id('karaoke') == 'karaoke_yellow'
    assert resolve_preset_id('bold-uppercase-v1') == 'karaoke_yellow'
    assert CaptionConfig().preset_id == 'karaoke_yellow'
    assert CaptionConfig(style_id='bold-uppercase-v1').preset_id == 'karaoke_yellow'
    with pytest.raises(ValidationError):
        CaptionConfig(preset_id='non_existent_style')


def test_four_presets_produce_distinct_ass_and_srt_outputs(tmp_path):
    t = transcript()
    s = Source(id=t.source_id, sha256=t.source_sha256, local_path=tmp_path / 's.mp4', duration_us=40_000_000)
    edl = plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]), t, s)
    builder = OpenShortsCaptionBuilder(tmp_path)

    outputs = {}
    for preset_id in VIDEO_STYLE_PRESETS:
        cfg = CaptionConfig(preset_id=preset_id, opening_text='Toda corrupção é igual?')
        caps = builder.build(t, edl, CaptionRevision(), cfg)
        assert caps.style_id == preset_id
        ass_text = caps.ass_path.read_text(encoding='utf-8')
        srt_text = caps.srt_path.read_text(encoding='utf-8-sig')
        outputs[preset_id] = (caps, ass_text, srt_text)

    # All 4 ASS files must be distinct in both style definitions and dialogue events
    ass_contents = [outputs[k][1] for k in VIDEO_STYLE_PRESETS]
    assert len(set(ass_contents)) == 4

    # 1. Karaokê Amarelo: yellow active word (&H00CCFF&), uppercase, yellow opening box (&H0000CCFF) with black text (&H00000000)
    _, ass_ky, _ = outputs['karaoke_yellow']
    assert r'\c&H00CCFF&' in ass_ky
    assert 'Style: Opening,Montserrat ExtraBold,10,&H00000000,&H00000000,&H0000CCFF,&H0000CCFF' in ass_ky
    ky_dialogues = [line for line in ass_ky.splitlines() if line.startswith('Dialogue: 0,')]
    assert all(line.count(r'\c&H00CCFF&') == 1 for line in ky_dialogues)

    # 2. Editorial Sóbrio: static blocks (fewer dialogues than word count, no inline color flashes), natural casing preserved
    caps_es, ass_es, srt_es = outputs['editorial_sober']
    es_dialogues = [line for line in ass_es.splitlines() if line.startswith('Dialogue: 0,')]
    assert len(es_dialogues) < len(ky_dialogues)
    assert all(r'\c&H' not in line for line in es_dialogues)
    assert all(r'\fad(90,90)' in line for line in es_dialogues)
    assert any(w.display_text != w.display_text.upper() for w in caps_es.words)
    assert any(ch.islower() for ch in srt_es)
    es_opening = [line for line in ass_es.splitlines() if line.startswith('Dialogue: 1,')]
    assert all(r'\move(' not in line and r'\pos(192,26)' in line for line in es_opening)
    assert 'Toda corrupção é igual?' in es_opening[0]

    # 3. Documental: lower-third box (BorderStyle=3, margin_v=26), dark & steel-blue palette (&HA8784A& marker)
    _, ass_doc, _ = outputs['documentary']
    doc_default_style = next(line for line in ass_doc.splitlines() if line.startswith('Style: Default,'))
    assert ',3,4,0,2,10,10,26,1' in doc_default_style
    doc_dialogues = [line for line in ass_doc.splitlines() if line.startswith('Dialogue: 0,')]
    assert len(doc_dialogues) < len(ky_dialogues)
    assert all(r'{\c&HA8784A&}▍ {\c&HFAF6F0&}' in line for line in doc_dialogues)
    doc_opening = [line for line in ass_doc.splitlines() if line.startswith('Dialogue: 1,')]
    assert r'\move(176,25,192,25' in doc_opening[0]

    # 4. Impacto: coral highlight (&H365AFF&) with kinetic scale animation (\t(0,95,\fscx112\fscy112))
    _, ass_imp, _ = outputs['impact']
    imp_dialogues = [line for line in ass_imp.splitlines() if line.startswith('Dialogue: 0,')]
    assert len(imp_dialogues) == len(ky_dialogues)
    assert all(r'\c&H365AFF&\fscx94\fscy94\t(0,95,\fscx112\fscy112)' in line for line in imp_dialogues)
    imp_opening = [line for line in ass_imp.splitlines() if line.startswith('Dialogue: 1,')]
    assert r'\fscx92\fscy92\t(0,' in imp_opening[0]
    assert 'Style: Opening,Montserrat ExtraBold,10,&H00FFFFFF,&H00FFFFFF,&H10365AFF,&H10140E10' in ass_imp
