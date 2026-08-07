from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"
W, H = 1080, 1920
FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]
FONT_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]
FONT_BOLD = next(Path(p) for p in FONT_BOLD_CANDIDATES if Path(p).exists())
FONT_REGULAR = next(Path(p) for p in FONT_REGULAR_CANDIDATES if Path(p).exists())


def run(cmd: list[str], timeout: int = 900, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        timeout=timeout,
    )


def safe_name(text: str) -> str:
    text = text.lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:90]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).replace("  ", " ").strip()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 1_000_000:
        print(f"Reusing {destination}")
        return
    headers = {"User-Agent": "Mozilla/5.0 LAOS editorial clip builder"}
    with requests.get(url, stream=True, timeout=90, headers=headers) as response:
        response.raise_for_status()
        with destination.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    if destination.stat().st_size < 1_000_000:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {destination}")


def ffprobe_duration(path: Path) -> float:
    result = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture=True)
    return float(result.stdout.strip())


def transcribe(source: Path, model_name: str) -> list[dict[str, Any]]:
    from faster_whisper import WhisperModel

    print(f"Loading Whisper model {model_name}", flush=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(source), language="en", beam_size=3, vad_filter=True,
        word_timestamps=False,
    )
    rows = []
    for seg in segments:
        rows.append({"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()})
    print(f"Transcribed {len(rows)} segments ({info.duration:.1f}s)")
    return rows


def find_quote(segments: list[dict[str, Any]], quote: str) -> tuple[float, float, str, float]:
    target = normalize(quote)
    best: tuple[float, float, str, float] | None = None
    for i in range(len(segments)):
        text_parts: list[str] = []
        for j in range(i, min(len(segments), i + 8)):
            text_parts.append(segments[j]["text"])
            candidate = " ".join(text_parts)
            score = max(
                fuzz.ratio(target, normalize(candidate)),
                fuzz.partial_ratio(target, normalize(candidate)),
                fuzz.token_set_ratio(target, normalize(candidate)),
            )
            item = (segments[i]["start"], segments[j]["end"], candidate, float(score))
            if best is None or score > best[3]:
                best = item
    if best is None:
        raise RuntimeError("No transcription segments were produced")
    print(f"Best quote match: {best[3]:.1f}% @ {best[0]:.2f}-{best[1]:.2f}: {best[2]}")
    if best[3] < 62:
        raise RuntimeError(f"Quote match confidence too low: {best[3]:.1f}")
    start = max(0.0, best[0] - 0.65)
    end = best[1] + 0.85
    if end - start > 10.5:
        end = start + 10.5
    return start, end, best[2], best[3]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def wrap_pixel(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered(draw: ImageDraw.ImageDraw, lines: list[str], fnt: ImageFont.FreeTypeFont,
                  y: int, fill: tuple[int, int, int, int], spacing: int = 12) -> int:
    for line in lines:
        box = draw.textbbox((0, 0), line, font=fnt)
        x = (W - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=fnt, fill=fill, stroke_width=2, stroke_fill=(0, 0, 0, 160))
        y += (box[3] - box[1]) + spacing
    return y


def overlay_base(item: dict[str, Any], progress_label: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((44, 44, 436, 104), radius=30, fill=(8, 14, 25, 215), outline=(70, 170, 255, 155), width=2)
    d.text((70, 62), f"{item['account']} · {item['series']}", font=font(24, True), fill=(245, 249, 255, 255))
    d.rounded_rectangle((832, 45, 1035, 103), radius=28, fill=(30, 110, 235, 225))
    b = d.textbbox((0, 0), progress_label, font=font(22, True))
    d.text((934 - (b[2]-b[0])/2, 64), progress_label, font=font(22, True), fill=(255,255,255,255))
    d.text((52, H-60), "Courtesy NASA/JPL-Caltech · análisis editorial · sin afiliación", font=font(18), fill=(235,240,248,220))
    return img, d


def make_soundbite_overlay(item: dict[str, Any], out: Path) -> None:
    img, d = overlay_base(item, "CLIP REAL")
    d.rounded_rectangle((54, 1220, 1026, 1812), radius=38, fill=(3, 7, 13, 190), outline=(255,255,255,35), width=2)
    title_f = font(66, True)
    y = 1265
    y = draw_centered(d, wrap_pixel(d, item["title"], title_f, 880), title_f, y, (255,255,255,255), 8)
    y += 36
    sub_f = font(37, True)
    draw_centered(d, wrap_pixel(d, item["quote_es"], sub_f, 860), sub_f, y, (255,219,91,255), 12)
    img.save(out)


def make_analysis_overlay(item: dict[str, Any], card: str, number: int, total: int, out: Path) -> None:
    img, d = overlay_base(item, f"{number}/{total}")
    d.rounded_rectangle((64, 1045, 1016, 1798), radius=44, fill=(4, 10, 19, 218), outline=(69, 171, 255, 110), width=3)
    d.rounded_rectangle((105, 1100, 245, 1160), radius=28, fill=(40, 128, 255, 230))
    d.text((142, 1115), f"IDEA {number}", font=font(24, True), fill=(255,255,255,255))
    card_f = font(55, True)
    lines = wrap_pixel(d, card, card_f, 820)
    total_h = len(lines) * 72
    draw_centered(d, lines, card_f, 1350 - total_h//2, (250,252,255,255), 13)
    img.save(out)


def make_cta_overlay(item: dict[str, Any], out: Path) -> None:
    img, d = overlay_base(item, "CONCLUSIÓN")
    d.rounded_rectangle((62, 1080, 1018, 1800), radius=48, fill=(4, 10, 19, 226), outline=(69, 171, 255, 140), width=3)
    d.text((120, 1140), "LA LECCIÓN", font=font(30, True), fill=(77,180,255,255))
    cta_f = font(64, True)
    lines = wrap_pixel(d, item["cta"], cta_f, 830)
    draw_centered(d, lines, cta_f, 1300, (255,255,255,255), 14)
    d.rounded_rectangle((245, 1660, 835, 1735), radius=36, fill=(40,128,255,235))
    label = "GUARDA · COMENTA · COMPARTE"
    bb = d.textbbox((0,0), label, font=font(26, True))
    d.text(((W-(bb[2]-bb[0]))/2, 1684), label, font=font(26, True), fill=(255,255,255,255))
    img.save(out)


def render_vertical(source: Path, start: float, duration: float, overlay: Path,
                    output: Path, with_audio: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filters = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=35:1[bg2];"
        "[fg]scale=1000:1500:force_original_aspect_ratio=decrease[fg2];"
        "[bg2][fg2]overlay=(W-w)/2:(H-h)/2[scene];"
        "[scene][1:v]overlay=0:0,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(source),
        "-loop", "1", "-i", str(overlay),
    ]
    if not with_audio:
        cmd += ["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    cmd += ["-filter_complex", filters, "-map", "[v]"]
    if with_audio:
        cmd += ["-map", "0:a?", "-af", "loudnorm=I=-15:LRA=11:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-ac", "2"]
    else:
        cmd += ["-map", "2:a", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-shortest", str(output)]
    run(cmd)


def tts(text: str, output: Path) -> None:
    try:
        run([sys.executable, "-m", "edge_tts", "--voice", "es-ES-AlvaroNeural", "--rate", "+4%", "--text", text, "--write-media", str(output)], timeout=180)
        if output.exists() and output.stat().st_size > 10_000:
            return
    except Exception as exc:
        print(f"edge-tts failed, using espeak-ng: {exc}")
    wav = output.with_suffix(".wav")
    run(["espeak-ng", "-v", "es", "-s", "165", "-p", "48", "-w", str(wav), text])
    run(["ffmpeg", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "160k", str(output)])


def attach_narration(video: Path, narration: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(narration),
        "-filter_complex", "[0:a]volume=0.08[a0];[1:a]loudnorm=I=-15:LRA=11:TP=-1.5,aresample=48000[a1];[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest", str(output)
    ])


def concat_mp4(parts: list[Path], output: Path) -> None:
    listing = output.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(output)])


def build_one(item: dict[str, Any], model_name: str) -> dict[str, Any]:
    item_work = WORK / item["id"]
    item_work.mkdir(parents=True, exist_ok=True)
    source = item_work / "source.m4v"
    download(item["media_url"], source)
    source_duration = ffprobe_duration(source)
    transcript_file = item_work / "transcript.json"
    if transcript_file.exists():
        segments = json.loads(transcript_file.read_text(encoding="utf-8"))
    else:
        segments = transcribe(source, model_name)
        transcript_file.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    start, end, matched, score = find_quote(segments, item["quote_en"])
    sound_duration = end - start

    sound_overlay = item_work / "soundbite.png"
    make_soundbite_overlay(item, sound_overlay)
    sound_part = item_work / "01_soundbite.mp4"
    render_vertical(source, start, sound_duration, sound_overlay, sound_part, True)

    narration_text = item["analysis_voice"] + " " + item["cta"]
    narration = item_work / "narration.mp3"
    tts(narration_text, narration)
    narr_duration = ffprobe_duration(narration) + 0.6
    cards = list(item["cards"])
    card_duration = max(4.2, narr_duration / len(cards))
    analysis_parts: list[Path] = []
    candidate_positions = [0.12, 0.38, 0.68, 0.82]
    for idx, card in enumerate(cards, start=1):
        pos = candidate_positions[(idx-1) % len(candidate_positions)] * max(1.0, source_duration - card_duration - 1)
        if abs(pos - start) < sound_duration + 2:
            pos = min(max(0.0, source_duration - card_duration - 1), pos + sound_duration + 4)
        overlay = item_work / f"card_{idx}.png"
        make_analysis_overlay(item, card, idx, len(cards), overlay)
        part = item_work / f"analysis_{idx}.mp4"
        render_vertical(source, pos, card_duration, overlay, part, False)
        analysis_parts.append(part)

    analysis_silent = item_work / "02_analysis_silent.mp4"
    concat_mp4(analysis_parts, analysis_silent)
    analysis_with_voice = item_work / "02_analysis.mp4"
    attach_narration(analysis_silent, narration, analysis_with_voice)

    cta_overlay = item_work / "cta.png"
    make_cta_overlay(item, cta_overlay)
    cta_part = item_work / "03_cta.mp4"
    cta_start = min(max(0.0, source_duration - 4.0), max(end + 2, source_duration * 0.88))
    render_vertical(source, cta_start, 3.4, cta_overlay, cta_part, False)

    final = OUTPUT / f"{item['id']}_{safe_name(item['title'])}.mp4"
    concat_mp4([sound_part, analysis_with_voice, cta_part], final)
    cover = OUTPUT / f"{item['id']}_{safe_name(item['title'])}.jpg"
    run(["ffmpeg", "-y", "-i", str(final), "-ss", "0.8", "-frames:v", "1", "-q:v", "2", str(cover)])

    result = {
        "id": item["id"],
        "title": item["title"],
        "account": item["account"],
        "series": item["series"],
        "source_page": item["source_page"],
        "media_url": item["media_url"],
        "credit": "Courtesy NASA/JPL-Caltech",
        "quote_match_score": round(score, 1),
        "quote_matched": matched,
        "source_start": round(start, 2),
        "source_end": round(end, 2),
        "output": final.name,
        "cover": cover.name,
        "duration_seconds": round(ffprobe_duration(final), 2),
        "rights_note": "Editorial/informational use; retain credit; do not imply NASA/JPL/Caltech endorsement; review identifiable-person commercial use before paid advertising.",
    }
    (OUTPUT / f"{item['id']}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(ROOT / "manifest.json"))
    parser.add_argument("--model", default="tiny.en")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    results = []
    for item in manifest:
        print(f"\n=== Building {item['id']}: {item['title']} ===", flush=True)
        results.append(build_one(item, args.model))
    (OUTPUT / "manifest-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
