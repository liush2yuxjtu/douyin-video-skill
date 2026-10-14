#!/usr/bin/env python3
"""Verify a cloned-voice voiceover against its script and the speaker's real voice.
校验克隆配音：逐句转写对稿、音高/语速对比真人、停顿/尾部垃圾、峰值与响度。

usage: verify_voiceover.py --full vo_full.wav --clips final/ --lines lines.txt --ref ref_real.wav
       [--nouns 杜威,默顿,...] [--model base] [--sim 0.8] [--warn-sim 0.9]
exit 0 = no FAIL (WARN allowed). Needs ffmpeg, numpy, faster-whisper.
"""
import argparse, difflib, glob, os, re, subprocess, sys
import numpy as np

SR = 16000
DIG = dict(zip("0123456789", "零一二三四五六七八九"))
rows = []


def add(status, check, detail):
    rows.append((status, check, detail))


def load(p):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32)


def norm(t, nouns=()):
    t = re.sub(r"\d", lambda m: DIG[m.group()], t)
    for n in nouns:
        t = t.replace(n, "")
    t = re.sub(r"[^\w]", "", t).replace("_", "")
    return t.upper()


def f0(x):
    fr, hop = int(.04 * SR), int(.01 * SR)
    th = 0.05 * (np.abs(x).max() + 1e-9)
    lo, hi = SR // 400, SR // 70
    out = []
    for i in range(0, len(x) - fr, hop):
        w = x[i:i + fr]
        if np.sqrt((w ** 2).mean()) < th:
            continue
        w = w - w.mean()
        ac = np.correlate(w, w, "full")[fr - 1:]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.5 * ac[0]:
            out.append(SR / k)
    return np.array(out)


def silences(x, thr_db=-40, min_len=0.25):
    """return list of (start,end) seconds of non-speech, energy-based, relative to clip peak"""
    hop = int(.02 * SR)
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    ref = e.max() + 1e-9
    quiet = 20 * np.log10(e / ref + 1e-9) < thr_db
    out, s = [], None
    for i, q in enumerate(list(quiet) + [False]):
        if q and s is None:
            s = i
        elif not q and s is not None:
            if (i - s) * .02 >= min_len:
                out.append((s * .02, i * .02))
            s = None
    return out


def loud(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    pk = float(re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", r)[-1])
    return i, pk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--clips", required=True, help="dir of per-sentence clips, sorted by name = line order")
    ap.add_argument("--lines", required=True, help="script, one sentence per line")
    ap.add_argument("--ref", required=True, help="real-voice recording of the speaker")
    ap.add_argument("--nouns", default="", help="comma list of proper nouns often mis-ASR'd (ignored in similarity)")
    ap.add_argument("--model", default="base")
    ap.add_argument("--sim", type=float, default=0.80, help="FAIL below")
    ap.add_argument("--warn-sim", type=float, default=0.90, help="WARN below")
    ap.add_argument("--pitch-tol", type=float, default=0.10)
    ap.add_argument("--rate-tol", type=float, default=0.20)
    ap.add_argument("--max-gap", type=float, default=1.5, help="max silence in full file (s)")
    ap.add_argument("--max-clip-gap", type=float, default=1.0, help="max inner/trailing silence per clip (s)")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--lufs-tol", type=float, default=1.5)
    ap.add_argument("--peak", type=float, default=-1.0)
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="float32", cpu_threads=2)
    nouns = [n for n in a.nouns.split(",") if n]

    def asr(x):
        segs = list(m.transcribe(x, language="zh", beam_size=5, vad_filter=True,
                                 initial_prompt="以下是普通话的句子。")[0])
        return "".join(s.text for s in segs), segs

    lines = [l.strip() for l in open(a.lines, encoding="utf-8") if l.strip()]
    clips = sorted(glob.glob(os.path.join(a.clips, "*.wav")))
    if len(clips) != len(lines):
        add("FAIL", "clip count", f"{len(clips)} clips vs {len(lines)} lines")

    # reference
    xr = load(a.ref)
    _, rsegs = asr(xr)
    rate_seg = [len(norm(s.text)) / max(s.end - s.start, .1) for s in rsegs if s.end - s.start > 2]
    ref_f0 = float(np.median(f0(xr)))
    rlo, rhi = min(rate_seg) * (1 - a.rate_tol), max(rate_seg) * (1 + a.rate_tol)
    print(f"reference: {len(xr)/SR:.1f}s f0={ref_f0:.0f}Hz rate={min(rate_seg):.2f}-{max(rate_seg):.2f} c/s")
    if len(xr) / SR < 15:
        add("WARN", "reference length", f"{len(xr)/SR:.1f}s < 15s (need 20-30s natural speech)")

    # per sentence
    for i, (c, line) in enumerate(zip(clips, lines), 1):
        x = load(c)
        t, segs = asr(x)
        sim = difflib.SequenceMatcher(None, norm(line, nouns), norm(t, nouns)).ratio()
        st = "PASS" if sim >= a.warn_sim else ("WARN" if sim >= a.sim else "FAIL")
        add(st, f"s{i:02d} text sim={sim:.2f}", f"ASR: {t}")
        dur = len(x) / SR
        sil = silences(x)
        inner = [e - s for s, e in sil if s > 0.05]
        tail = [e - s for s, e in sil if e >= dur - 0.05]
        worst = max(inner + [0])
        exp = len(norm(line)) / 2.0 + 2.5          # generous: 2 chars/s + 2.5s lead/tail
        if dur > exp:
            add("FAIL", f"s{i:02d} duration", f"{dur:.1f}s > {exp:.1f}s for {len(norm(line))} chars (junk / prompt read aloud?)")
        if worst > a.max_clip_gap:
            add("FAIL" if (not tail or worst not in tail or worst > 2 * a.max_clip_gap) else "WARN",
                f"s{i:02d} silence", f"longest silence {worst:.2f}s > {a.max_clip_gap}s")
        cpk = 20 * np.log10(np.abs(x).max() + 1e-9)
        if cpk >= -0.1:
            add("WARN", f"s{i:02d} raw clip peak", f"{cpk:.1f} dBFS (possible clipping in source take)")

    # full file
    x = load(a.full)
    t, segs = asr(x)
    script = "".join(lines)
    sim = difflib.SequenceMatcher(None, norm(script, nouns), norm(t, nouns)).ratio()
    add("PASS" if sim >= a.warn_sim else ("WARN" if sim >= a.sim else "FAIL"), f"full text sim={sim:.2f}", f"{len(norm(t))}/{len(norm(script))} chars")
    vf0 = float(np.median(f0(x)))
    d = vf0 / ref_f0 - 1
    add("PASS" if abs(d) <= a.pitch_tol else "FAIL", "pitch median", f"{vf0:.0f}Hz vs ref {ref_f0:.0f}Hz ({d:+.0%}, tol ±{a.pitch_tol:.0%})")
    sp = sum(s.end - s.start for s in segs)
    rate = len(norm(t)) / max(sp, .1)
    add("PASS" if rlo <= rate <= rhi else "FAIL", "speech rate", f"{rate:.2f} c/s, allowed {rlo:.2f}-{rhi:.2f}")
    gaps = [e - s for s, e in silences(x)]
    g = max(gaps + [0])
    add("PASS" if g <= a.max_gap else "FAIL", "max gap (full)", f"{g:.2f}s (limit {a.max_gap}s)")
    i_lufs, pk = loud(a.full)
    add("PASS" if pk <= a.peak else "FAIL", "true peak", f"{pk:.1f} dBFS (limit {a.peak})")
    add("PASS" if abs(i_lufs - a.lufs) <= a.lufs_tol else "FAIL", "loudness", f"{i_lufs:.1f} LUFS (target {a.lufs}±{a.lufs_tol})")

    print(f"\n{'STATUS':6}  {'CHECK':26}  DETAIL")
    for s, c, dd in rows:
        print(f"{s:6}  {c:26}  {dd}")
    nf = sum(r[0] == "FAIL" for r in rows)
    nw = sum(r[0] == "WARN" for r in rows)
    print(f"\nRESULT: {'FAIL' if nf else 'PASS'}  (fail={nf} warn={nw})")
    if nouns:
        print("note: proper nouns ignored in similarity:", ",".join(nouns))
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
