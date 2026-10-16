"""Centralized, versioned catalog of the four fixed video style presets."""
from dataclasses import dataclass
from typing import Literal

PRESET_CATALOG_VERSION = 1

PresetId = Literal['karaoke_yellow', 'editorial_sober', 'documentary', 'impact']
LegacyPresetId = Literal['karaoke_yellow', 'editorial_sober', 'documentary', 'impact', 'bold-uppercase-v1', 'karaoke']
CaptionMode = Literal['karaoke', 'static', 'lower_third', 'kinetic_impact']
OpeningMode = Literal['yellow_band', 'sober_card', 'documentary_band', 'kinetic_coral']

DEFAULT_PRESET_ID: PresetId = 'karaoke_yellow'

LEGACY_PRESET_ALIASES: dict[str, PresetId] = {
    'bold-uppercase-v1': 'karaoke_yellow',
    'karaoke': 'karaoke_yellow',
}

PlaybackSpeed = Literal['1x', '1.25x', '1.5x']
DEFAULT_PLAYBACK_SPEED: PlaybackSpeed = '1x'
PLAYBACK_SPEED_RATIONAL: dict[PlaybackSpeed, tuple[Literal[1, 5, 3], Literal[1, 4, 2]]] = {
    '1x': (1, 1),
    '1.25x': (5, 4),
    '1.5x': (3, 2),
}


def validate_playback_speed(value: str | None) -> PlaybackSpeed:
    """Strictly validate that value is one of the 3 supported playback speeds."""
    if not value:
        return DEFAULT_PLAYBACK_SPEED
    if value not in PLAYBACK_SPEED_RATIONAL:
        raise ValueError(f'Invalid playback speed: {value!r}. Supported speeds: 1x, 1.25x, 1.5x')
    return value  # type: ignore[return-value]


def speed_ratio_to_label(speed_num: int, speed_den: int) -> PlaybackSpeed:
    for label, (num, den) in PLAYBACK_SPEED_RATIONAL.items():
        if num == speed_num and den == speed_den:
            return label
    return '1x'



@dataclass(frozen=True)
class CaptionStyleSpec:
    mode: CaptionMode
    uppercase: bool
    font_name: str
    fontsize: int
    bold: int
    font_color: str
    highlight_color: str
    border_color: str
    border_width: int
    bg_color: str
    bg_opacity: float
    shadow: int
    alignment: str
    margin_v: int
    letter_spacing: int
    max_chars: int
    max_duration: float
    max_words: int
    effect: str = 'none'
    accent_prefix: str = ''
    fade_ms: int = 0


@dataclass(frozen=True)
class OpeningStyleSpec:
    mode: OpeningMode
    uppercase: bool
    font_name: str
    size: int
    long_size: int
    bold: int
    primary_colour: str
    secondary_colour: str
    outline_colour: str
    back_colour: str
    border_style: int
    outline: int
    shadow: int
    alignment: int
    margin_l: int
    margin_r: int
    margin_v: int
    spacing: int
    wrap_width: int
    long_wrap_width: int
    accent_prefix: str = ''


@dataclass(frozen=True)
class VideoStylePreset:
    id: PresetId
    version: int
    label: str
    description: str
    caption: CaptionStyleSpec
    opening: OpeningStyleSpec


VIDEO_STYLE_PRESETS: dict[PresetId, VideoStylePreset] = {
    'karaoke_yellow': VideoStylePreset(
        id='karaoke_yellow',
        version=PRESET_CATALOG_VERSION,
        label='Karaokê Amarelo',
        description='Palavras ativas amarelas e título inicial com fundo amarelo e texto preto.',
        caption=CaptionStyleSpec(
            mode='karaoke',
            uppercase=True,
            font_name='Montserrat ExtraBold',
            fontsize=22,
            bold=1,
            font_color='#FFFFFF',
            highlight_color='#FFCC00',
            border_color='#000000',
            border_width=3,
            bg_color='#000000',
            bg_opacity=0.0,
            shadow=0,
            alignment='bottom',
            margin_v=43,
            letter_spacing=0,
            max_chars=32,
            max_duration=2.0,
            max_words=3,
            effect='none',
        ),
        opening=OpeningStyleSpec(
            mode='yellow_band',
            uppercase=True,
            font_name='Montserrat ExtraBold',
            size=10,
            long_size=9,
            bold=1,
            primary_colour='&H00000000',
            secondary_colour='&H00000000',
            outline_colour='&H0000CCFF',
            back_colour='&H0000CCFF',
            border_style=3,
            outline=4,
            shadow=0,
            alignment=8,
            margin_l=20,
            margin_r=20,
            margin_v=24,
            spacing=0,
            wrap_width=25,
            long_wrap_width=30,
        ),
    ),
    'editorial_sober': VideoStylePreset(
        id='editorial_sober',
        version=PRESET_CATALOG_VERSION,
        label='Editorial Sóbrio',
        description='Legendas estáticas, tipografia discreta e visual formal.',
        caption=CaptionStyleSpec(
            mode='static',
            uppercase=False,
            font_name='Montserrat ExtraBold',
            fontsize=19,
            bold=0,
            font_color='#F5F3EE',
            highlight_color='#F5F3EE',
            border_color='#18181B',
            border_width=2,
            bg_color='#141418',
            bg_opacity=0.0,
            shadow=1,
            alignment='bottom',
            margin_v=38,
            letter_spacing=1,
            max_chars=38,
            max_duration=2.6,
            max_words=5,
            effect='none',
            fade_ms=90,
        ),
        opening=OpeningStyleSpec(
            mode='sober_card',
            uppercase=False,
            font_name='Montserrat ExtraBold',
            size=9,
            long_size=8,
            bold=0,
            primary_colour='&H00EEF3F5',
            secondary_colour='&H00EEF3F5',
            outline_colour='&H18201E1C',
            back_colour='&H18201E1C',
            border_style=3,
            outline=5,
            shadow=0,
            alignment=8,
            margin_l=24,
            margin_r=24,
            margin_v=26,
            spacing=1,
            wrap_width=28,
            long_wrap_width=32,
        ),
    ),
    'documentary': VideoStylePreset(
        id='documentary',
        version=PRESET_CATALOG_VERSION,
        label='Documental',
        description='Legendas em faixa inferior, com paleta escura e azul-aço.',
        caption=CaptionStyleSpec(
            mode='lower_third',
            uppercase=False,
            font_name='Montserrat ExtraBold',
            fontsize=18,
            bold=1,
            font_color='#F0F6FA',
            highlight_color='#4A78A8',
            border_color='#141E28',
            border_width=4,
            bg_color='#141E28',
            bg_opacity=0.88,
            shadow=0,
            alignment='bottom',
            margin_v=26,
            letter_spacing=0,
            max_chars=38,
            max_duration=2.6,
            max_words=5,
            effect='none',
            accent_prefix=r'{\c&HA8784A&}▍ {\c&HFAF6F0&}',
            fade_ms=70,
        ),
        opening=OpeningStyleSpec(
            mode='documentary_band',
            uppercase=True,
            font_name='Montserrat ExtraBold',
            size=9,
            long_size=8,
            bold=1,
            primary_colour='&H00FAF6F0',
            secondary_colour='&H00A8784A',
            outline_colour='&H146E4A24',
            back_colour='&H14281E14',
            border_style=3,
            outline=5,
            shadow=0,
            alignment=8,
            margin_l=20,
            margin_r=20,
            margin_v=25,
            spacing=1,
            wrap_width=26,
            long_wrap_width=30,
            accent_prefix=r'{\c&HA8784A&}▍ {\c&HFAF6F0&}',
        ),
    ),
    'impact': VideoStylePreset(
        id='impact',
        version=PRESET_CATALOG_VERSION,
        label='Impacto',
        description='Cor coral, destaque cinético e animações discretas.',
        caption=CaptionStyleSpec(
            mode='kinetic_impact',
            uppercase=True,
            font_name='Montserrat ExtraBold',
            fontsize=23,
            bold=1,
            font_color='#FFFFFF',
            highlight_color='#FF5A36',
            border_color='#100E14',
            border_width=4,
            bg_color='#100E14',
            bg_opacity=0.0,
            shadow=1,
            alignment='bottom',
            margin_v=45,
            letter_spacing=1,
            max_chars=28,
            max_duration=1.8,
            max_words=3,
            effect='kinetic',
        ),
        opening=OpeningStyleSpec(
            mode='kinetic_coral',
            uppercase=True,
            font_name='Montserrat ExtraBold',
            size=10,
            long_size=9,
            bold=1,
            primary_colour='&H00FFFFFF',
            secondary_colour='&H00FFFFFF',
            outline_colour='&H10365AFF',
            back_colour='&H10140E10',
            border_style=3,
            outline=5,
            shadow=0,
            alignment=8,
            margin_l=20,
            margin_r=20,
            margin_v=24,
            spacing=1,
            wrap_width=24,
            long_wrap_width=28,
        ),
    ),
}


def validate_known_preset_id(value: str) -> PresetId:
    """Strictly validate that value is one of the 4 official preset IDs."""
    if not isinstance(value, str) or value not in VIDEO_STYLE_PRESETS:
        raise ValueError(f'Unknown video style preset: {value!r}')
    return value  # type: ignore[return-value]


def resolve_preset_id(value: str | None) -> PresetId:
    """Resolve preset ID, mapping legacy style identifiers to karaoke_yellow."""
    if not value:
        return DEFAULT_PRESET_ID
    if value in LEGACY_PRESET_ALIASES:
        return LEGACY_PRESET_ALIASES[value]
    return validate_known_preset_id(value)


def get_preset(value: str | None = None) -> VideoStylePreset:
    return VIDEO_STYLE_PRESETS[resolve_preset_id(value)]


def list_presets() -> list[dict[str, object]]:
    return [
        {
            'id': preset.id,
            'version': preset.version,
            'label': preset.label,
            'description': preset.description,
        }
        for preset in VIDEO_STYLE_PRESETS.values()
    ]
