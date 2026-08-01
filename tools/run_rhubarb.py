#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from domain.rhubarb_config import rhubarb_bin, rhubarb_available
from domain.lipsync import cues_from_rhubarb
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('audio', type=Path, nargs='?', default=None)
    ap.add_argument('--dialog', type=str, default=None)
    ap.add_argument('--dialog-file', type=Path, default=None)
    ap.add_argument('-o', '--output', type=Path, default=None)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    print(f'rhubarb: {rhubarb_bin()} available={rhubarb_available()}')
    if args.check:
        return 0 if rhubarb_available() else 1
    if args.audio is None or not args.audio.is_file():
        print(f'missing audio: {args.audio}', file=sys.stderr)
        return 1
    transcript = args.dialog
    if args.dialog_file and args.dialog_file.is_file():
        transcript = args.dialog_file.read_text(encoding='utf-8')
    cues = cues_from_rhubarb(args.audio, transcript=transcript, work_dir=args.audio.parent)
    print(f'cues: {len(cues)}')
    for c in cues[:12]:
        print(f'  {c.timing.start:6.2f}-{c.timing.end:6.2f}  {c.value.value}')
    if args.output:
        payload = {'mouthCues': [{'start': c.timing.start, 'end': c.timing.end, 'value': c.value.value} for c in cues]}
        args.output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
