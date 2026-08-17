import random

from app.services.long_video import (
    build_ffmpeg_command,
    build_filter_complex,
    build_visual_filter,
    calculate_render_duration,
    select_random_playlist,
)


def test_random_playlist_repeats_without_consecutive_duplicates():
    paths, durations = select_random_playlist(
        ["a.mp3", "b.mp3"], [60.0, 60.0], 180.0, 5.0, random.Random(7)
    )

    assert calculate_render_duration(durations, 5.0)[1] >= 180.0
    assert all(left != right for left, right in zip(paths, paths[1:]))


def test_filters_contain_transition_brightness_and_watermark():
    visual = build_visual_filter([10.0, 12.0], "dissolve", 1.0)
    final = build_filter_complex(2, 3, 40, 50, 5.0, 0.25)

    assert "xfade=transition=dissolve:duration=1:offset=9" in visual
    assert "eq=brightness=0.25" in final
    assert "colorchannelmixer=aa=0.8" in final
    assert "[a0][a1]acrossfade=d=5:c1=tri:c2=tri[aout]" in final


def test_command_uses_direct_ffmpeg_with_long_video_settings(monkeypatch):
    monkeypatch.setattr("app.services.long_video.utils.get_ffmpeg_binary", lambda: "ffmpeg")
    command = build_ffmpeg_command(
        "base.mp4", ["one.mp3", "two.wav"], "mark.png", "final.mp4", 300.0, 10, 20
    )

    assert command[:5] == ["ffmpeg", "-hide_banner", "-y", "-stream_loop", "-1"]
    assert command[command.index("-t") + 1] == "300.000"
    assert command[command.index("-preset") + 1] == "veryfast"
    assert command[command.index("-b:a") + 1] == "320k"
    assert "libx264" in command
