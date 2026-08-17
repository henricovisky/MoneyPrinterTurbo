"""Renderização de vídeos longos usando somente FFmpeg/FFprobe."""

from __future__ import annotations

import os
import random
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from app.utils import utils

ProgressCallback = Callable[[float, str], None]
VIDEO_TRANSITIONS = {"none", "fade", "dissolve", "wipeleft", "slideright", "circleopen"}
MAX_VISUAL_CYCLE_SECONDS = 300.0


def get_ffprobe_binary() -> str:
    configured = os.environ.get("FFPROBE_EXE")
    if configured:
        return configured
    system_binary = shutil.which("ffprobe")
    if system_binary:
        return system_binary
    ffmpeg = Path(utils.get_ffmpeg_binary())
    sibling = ffmpeg.with_name("ffprobe" + ffmpeg.suffix)
    return str(sibling) if sibling.is_file() else "ffprobe"


def probe_duration(file_path: str | Path) -> float:
    """Retorna a duração de um arquivo de mídia em segundos."""
    try:
        result = subprocess.run(
            [
                get_ffprobe_binary(),
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        duration = float(result.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Não foi possível ler a duração de {file_path}: {exc}") from exc
    if duration <= 0:
        raise ValueError(f"O arquivo não possui duração válida: {file_path}")
    return duration


def calculate_render_duration(
    media_durations: Sequence[float], overlap_seconds: float
) -> tuple[float, float]:
    """Retorna (soma bruta, duração real após as sobreposições)."""
    if not media_durations:
        raise ValueError("Envie ao menos um arquivo de mídia.")
    if overlap_seconds < 0:
        raise ValueError("A duração da transição não pode ser negativa.")
    if len(media_durations) > 1 and min(media_durations) <= overlap_seconds:
        raise ValueError(
            "Cada arquivo deve ser mais longo que a transição "
            f"de {overlap_seconds:g} segundos."
        )
    total = sum(media_durations)
    return total, total - overlap_seconds * (len(media_durations) - 1)


def select_random_playlist(
    paths: Sequence[str | Path],
    durations: Sequence[float],
    target_duration: float,
    overlap_seconds: float,
    rng: random.Random | None = None,
) -> tuple[list[Path], list[float]]:
    """Sorteia arquivos, evitando repetição consecutiva, até cobrir o alvo."""
    if len(paths) != len(durations) or not paths:
        raise ValueError("Arquivos e durações devem possuir o mesmo tamanho.")
    if target_duration <= 0:
        raise ValueError("A duração final deve ser maior que zero.")
    calculate_render_duration(durations, overlap_seconds)

    chooser = rng or random.Random()
    selected_paths: list[Path] = []
    selected_durations: list[float] = []
    rendered_duration = 0.0
    last_index: int | None = None
    while rendered_duration < target_duration:
        choices = [index for index in range(len(paths)) if index != last_index]
        index = chooser.choice(choices or [0])
        selected_paths.append(Path(paths[index]))
        selected_durations.append(durations[index])
        _, rendered_duration = calculate_render_duration(
            selected_durations, overlap_seconds
        )
        last_index = index
    return selected_paths, selected_durations


def build_visual_filter(
    durations: Sequence[float], transition: str, transition_seconds: float
) -> str:
    """Cria o grafo do ciclo visual em 1080p."""
    if transition not in VIDEO_TRANSITIONS:
        raise ValueError(f"Transição de vídeo inválida: {transition}")
    overlap = 0.0 if transition == "none" else transition_seconds
    calculate_render_duration(durations, overlap)

    filters = []
    for index, duration in enumerate(durations):
        filters.append(
            f"[{index}:v]trim=duration={duration:g},setpts=PTS-STARTPTS,fps=30,"
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"format=yuv420p[v{index}]"
        )

    if len(durations) == 1:
        filters.append("[v0]null[vcycle]")
    elif transition == "none":
        inputs = "".join(f"[v{index}]" for index in range(len(durations)))
        filters.append(f"{inputs}concat=n={len(durations)}:v=1:a=0[vcycle]")
    else:
        previous = "v0"
        current_duration = durations[0]
        for index in range(1, len(durations)):
            output = "vcycle" if index == len(durations) - 1 else f"vx{index}"
            offset = current_duration - transition_seconds
            filters.append(
                f"[{previous}][v{index}]xfade=transition={transition}:"
                f"duration={transition_seconds:g}:offset={offset:g}[{output}]"
            )
            current_duration += durations[index] - transition_seconds
            previous = output
    return ";".join(filters)


def build_filter_complex(
    audio_count: int,
    watermark_input_index: int,
    watermark_x: int,
    watermark_y: int,
    crossfade_seconds: float,
    brightness: float = 0.0,
) -> str:
    """Monta filtros finais de brilho, watermark e crossfade de áudio."""
    if not -1.0 <= brightness <= 1.0:
        raise ValueError("O brilho deve estar entre -1 e 1.")
    filters = [
        "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
        f"eq=brightness={brightness:g}[base]",
        f"[{watermark_input_index}:v]format=rgba,colorchannelmixer=aa=0.8[watermark]",
        f"[base][watermark]overlay=x={watermark_x}:y={watermark_y}:format=auto[vout]",
    ]
    for index in range(audio_count):
        filters.append(
            f"[{index + 1}:a]aresample=48000,"
            f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{index}]"
        )
    if audio_count == 1:
        filters.append("[a0]anull[aout]")
    else:
        previous = "a0"
        for index in range(1, audio_count):
            output = "aout" if index == audio_count - 1 else f"mix{index}"
            filters.append(
                f"[{previous}][a{index}]acrossfade=d={crossfade_seconds:g}:"
                f"c1=tri:c2=tri[{output}]"
            )
            previous = output
    return ";".join(filters)


def build_ffmpeg_command(
    video_path: str | Path,
    audio_paths: Sequence[str | Path],
    watermark_path: str | Path,
    output_path: str | Path,
    duration: float,
    watermark_x: int,
    watermark_y: int,
    crossfade_seconds: float = 5.0,
    brightness: float = 0.0,
) -> list[str]:
    """Cria o comando final sem usar shell ou MoviePy."""
    command = [
        utils.get_ffmpeg_binary(),
        "-hide_banner",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(video_path),
    ]
    for audio_path in audio_paths:
        command.extend(["-i", str(audio_path)])
    command.extend(["-loop", "1", "-i", str(watermark_path)])
    command.extend(
        [
            "-filter_complex",
            build_filter_complex(
                len(audio_paths),
                len(audio_paths) + 1,
                watermark_x,
                watermark_y,
                crossfade_seconds,
                brightness,
            ),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "320k",
            "-movflags",
            "+faststart",
            "-progress",
            "pipe:1",
            "-nostats",
            "-loglevel",
            "error",
            str(output_path),
        ]
    )
    return command


def _time_to_seconds(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _run_ffmpeg(
    command: Sequence[str],
    output: Path,
    duration: float,
    on_progress: ProgressCallback | None,
    progress_start: float,
    progress_span: float,
    message: str,
) -> None:
    if on_progress:
        on_progress(progress_start, message)
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg não encontrado. Instale-o e adicione-o ao PATH.") from exc

    output_lines: list[str] = []
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.strip()
        if not line:
            continue
        output_lines.append(line)
        if line.startswith("out_time="):
            try:
                current = min(_time_to_seconds(line.partition("=")[2]), duration)
            except (TypeError, ValueError):
                continue
            if on_progress:
                fraction = progress_start + progress_span * current / duration
                on_progress(fraction, f"{message} {current:.0f}s / {duration:.0f}s")
    if process.wait() != 0:
        output.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg falhou:\n" + "\n".join(output_lines[-20:]))
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("O FFmpeg terminou sem produzir um arquivo válido.")


def render_visual_cycle(
    video_paths: Sequence[str | Path],
    output_path: str | Path,
    target_duration: float,
    transition: str,
    transition_seconds: float,
    rng: random.Random,
    on_progress: ProgressCallback | None,
) -> Path:
    """Cria um ciclo visual aleatório curto que será repetido na saída longa."""
    durations = [probe_duration(path) for path in video_paths]
    overlap = (
        0.0
        if transition == "none"
        else min(transition_seconds, min(durations) / 2)
    )
    selected, selected_durations = select_random_playlist(
        video_paths,
        durations,
        min(target_duration, MAX_VISUAL_CYCLE_SECONDS),
        overlap,
        rng,
    )
    if len(selected) == 1:
        return selected[0]

    _, cycle_duration = calculate_render_duration(selected_durations, overlap)
    output = Path(output_path)
    command = [utils.get_ffmpeg_binary(), "-hide_banner", "-y"]
    for path in selected:
        command.extend(["-i", str(path)])
    command.extend(
        [
            "-filter_complex",
            build_visual_filter(selected_durations, transition, overlap),
            "-map",
            "[vcycle]",
            "-an",
            "-t",
            f"{cycle_duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-progress",
            "pipe:1",
            "-nostats",
            "-loglevel",
            "error",
            str(output),
        ]
    )
    _run_ffmpeg(command, output, cycle_duration, on_progress, 0.0, 0.15, "Montando ciclo:")
    return output


def render_long_video(
    video_paths: Sequence[str | Path],
    audio_paths: Sequence[str | Path],
    watermark_path: str | Path,
    output_path: str | Path,
    watermark_x: int,
    watermark_y: int,
    target_duration: float,
    transition: str = "fade",
    brightness: float = 0.0,
    crossfade_seconds: float = 5.0,
    transition_seconds: float = 1.0,
    on_progress: ProgressCallback | None = None,
    rng: random.Random | None = None,
) -> tuple[float, int, int]:
    """Renderiza a duração escolhida e retorna duração e contagens selecionadas."""
    if not video_paths or not audio_paths:
        raise ValueError("Envie ao menos um vídeo e uma trilha de áudio.")
    paths = [*(Path(path) for path in video_paths), *(Path(path) for path in audio_paths)]
    paths.append(Path(watermark_path))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Arquivos não encontrados: {', '.join(missing)}")

    chooser = rng or random.Random()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    visual_cycle = render_visual_cycle(
        video_paths,
        output.with_name("visual-cycle.mp4"),
        target_duration,
        transition,
        transition_seconds,
        chooser,
        on_progress,
    )
    audio_durations = [probe_duration(path) for path in audio_paths]
    effective_crossfade = min(crossfade_seconds, min(audio_durations) / 2)
    selected_audio, _ = select_random_playlist(
        audio_paths,
        audio_durations,
        target_duration,
        effective_crossfade,
        chooser,
    )
    command = build_ffmpeg_command(
        visual_cycle,
        selected_audio,
        watermark_path,
        output,
        target_duration,
        int(watermark_x),
        int(watermark_y),
        effective_crossfade,
        brightness,
    )
    _run_ffmpeg(
        command,
        output,
        target_duration,
        on_progress,
        0.15,
        0.85,
        "Renderizando vídeo final:",
    )
    if on_progress:
        on_progress(1.0, "Renderização concluída.")
    return target_duration, len(selected_audio), len(video_paths)
