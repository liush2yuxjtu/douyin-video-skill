#!/usr/bin/env python3
"""Verify a cloned-voice voiceover against its script and the speaker's real voice.
校验克隆配音：逐句转写对稿、音高/语速对比真人、停顿/尾部垃圾、峰值与响度。

usage: verify_voiceover.py --full vo_full.wav --clips final/ --lines lines.txt --ref ref_real.wav
       [--nouns 杜威,默顿,...] [--model base] [--sim 0.8] [--warn-sim 0.9]
exit 0 = no FAIL (WARN allowed). Needs ffmpeg, numpy, faster-whisper; jieba for prosody checks.
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


PUNCT_END = set("。！？!?.…")
PUNCT = set("，。！？、；：,.!?;:…—「」『』“”\"'（）() ")


def script_boundaries(lines):
    """normalized script chars + boundary type after each char: end / comma / word / inside (jieba)."""
    import jieba
    jieba.setLogLevel(60)
    chars, bt = [], []
    for line in lines:
        for w in jieba.cut(line):
            if all(c in PUNCT for c in w):
                if bt and bt[-1] != "end":
                    bt[-1] = "end" if any(c in PUNCT_END for c in w) else "comma"
                continue
            n = norm(w)
            for k, c in enumerate(n):
                chars.append(c)
                bt.append("inside" if k < len(n) - 1 else "word")
        if bt:
            bt[-1] = "end"
    return chars, bt


def pause_list(x, min_len=0.08, rel=-30):
    hop = int(.01 * SR)
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(e + 1e-9)
    q = db < db.max() + rel
    out, s = [], None
    for i, v in enumerate(list(q) + [False]):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if (i - s) * .01 >= min_len and s > 0 and i < len(q):
                out.append((s * .01, i * .01))
            s = None
    return out


def prosody(m, x, lines):
    """Phrasing + intonation. Pauses are mapped to script boundaries via word timestamps (snapped +-1 char)."""
    segs = list(m.transcribe(x, language="zh", beam_size=5, vad_filter=False, word_timestamps=True,
                             initial_prompt="以下是普通话的句子。")[0])
    ac, at = [], []
    for sg in segs:
        for w in sg.words:
            n = norm(w.word)
            for k, c in enumerate(n):
                d = (w.end - w.start) / len(n)
                ac.append(c)
                at.append((w.start + k * d, w.start + (k + 1) * d))
    sc, bt = script_boundaries(lines)
    st = [None] * len(sc)
    for a, b, n in difflib.SequenceMatcher(None, sc, ac, autojunk=False).get_matching_blocks():
        for k in range(n):
            st[a + k] = at[b + k]
    known = [i for i, v in enumerate(st) if v]
    if len(known) < len(sc) * 0.5:
        return None
    for i in range(len(sc)):
        if st[i] is None:
            p = max([j for j in known if j < i], default=known[0])
            q = min([j for j in known if j > i], default=known[-1])
            st[i] = (st[p][1], st[q][0]) if p != q else st[p]
    rank = {"end": 0, "comma": 1, "word": 2, "inside": 3}
    breaks = []
    for s, e in pause_list(x):
        mid = (s + e) / 2
        cand = [i for i in range(len(sc) - 1) if st[i][1] <= mid + 0.08 and st[i + 1][0] >= mid - 0.08]
        i = min(cand, key=lambda i: abs((st[i][1] + st[i + 1][0]) / 2 - mid)) if cand else \
            int(np.argmin([abs(t[1] - mid) for t in st]))
        i = min(i, len(sc) - 2)
        i = min([j for j in (i - 1, i, i + 1) if 0 <= j < len(sc) - 1], key=lambda j: (rank[bt[j]], abs(j - i)))
        breaks.append(dict(t=s, dur=e - s, type=bt[i], ctx="".join(sc[max(0, i - 5):i + 1]) + "|" + "".join(sc[i + 1:i + 6])))
    # intonation per sentence (semitones re file median)
    hop = int(.01 * SR); fr = int(.04 * SR); lo, hi = SR // 400, SR // 70; th = 0.05 * np.abs(x).max()
    T, F = [], []
    for i in range(0, len(x) - fr, hop):
        w = x[i:i + fr]
        if np.sqrt((w ** 2).mean()) < th:
            continue
        w = w - w.mean(); acr = np.correlate(w, w, "full")[fr - 1:]; k = lo + int(np.argmax(acr[lo:hi]))
        if acr[k] > 0.5 * acr[0]:
            T.append(i / SR); F.append(SR / k)
    T, F = np.array(T), np.array(F)
    stv = 12 * np.log2(F / np.median(F))
    pos, rng, sd, fin = 0, [], [], []
    for line in lines:
        n = len(norm(line)); a, b = st[pos][0], st[pos + n - 1][1]; pos += n
        v = stv[(T >= a) & (T <= b)]
        if len(v) >= 10:
            q = max(3, len(v) // 4)
            rng.append(np.percentile(v, 95) - np.percentile(v, 5)); sd.append(v.std())
            fin.append(np.median(v[-q:]) - np.median(v[:-q]))
    return breaks, bt, float(np.mean(rng)), float(np.mean(sd)), fin


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
    ap.add_argument("--no-prosody", action="store_true", help="skip phrasing/intonation checks (needs jieba)")
    ap.add_argument("--min-comma-pause", type=float, default=0.30, help="FAIL if fewer commas get a pause (run-on)")
    ap.add_argument("--max-midphrase", type=float, default=0.15, help="FAIL on a non-punctuation pause >= this (s)")
    ap.add_argument("--min-f0-range", type=float, default=7.0, help="WARN if mean per-sentence f0 range (st) below")
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
    if not a.no_prosody:
        try:
            pr = prosody(m, x, lines)
        except ImportError:
            pr = "nojieba"
        if pr == "nojieba":
            add("WARN", "prosody", "skipped: pip install jieba")
        elif pr is None:
            add("WARN", "prosody", "skipped: transcript too far from script to align")
        else:
            br, bt, f0r, f0sd, fin = pr
            n_comma = sum(1 for b in bt[:-1] if b == "comma")
            commas = [b["dur"] for b in br if b["type"] == "comma"]
            ends = [b["dur"] for b in br if b["type"] == "end"]
            cov = len(commas) / n_comma if n_comma else 1
            add("PASS" if cov >= a.min_comma_pause else "FAIL", "phrasing: comma pauses",
                f"{len(commas)}/{n_comma} commas paused (<{a.min_comma_pause:.0%} = run-on, no breath at commas)")
            mid = [b for b in br if b["type"] in ("word", "inside") and b["dur"] >= a.max_midphrase]
            add("PASS" if not mid else "FAIL", "phrasing: mid-phrase breaks",
                "; ".join(f"{b['t']:.2f}s {b['dur']:.2f}s {b['ctx']}" for b in mid) or "none")
            em = float(np.mean(ends)) if ends else 0
            inv = [b for b in br if b["type"] != "end" and em and b["dur"] >= 0.9 * em]
            add("PASS" if not inv else "FAIL", "phrasing: pause hierarchy",
                f"sentence-end mean {em:.2f}s, comma mean {np.mean(commas) if commas else 0:.2f}s; inverted: " +
                ("; ".join(f"{b['t']:.2f}s {b['dur']:.2f}s {b['ctx']}" for b in inv) or "none"))
            add("PASS" if f0r >= a.min_f0_range else "WARN", "intonation: f0 range",
                f"{f0r:.1f} st per sentence (sd {f0sd:.1f}); phrase-final moves " + ",".join(f"{v:+.1f}" for v in fin))
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
