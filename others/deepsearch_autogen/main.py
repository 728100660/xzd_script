import argparse
import json
from datetime import datetime
from pathlib import Path

from .orchestrator import run_deepsearch


def save_output(output_dir: Path, question: str, answer: str, transcript):
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_q = "".join(c for c in question if c.isalnum() or c in (" ", "-", "_"))[:60].strip().replace(" ", "_")
    base = output_dir / f"deepsearch_{ts}_{safe_q}"
    (base.with_suffix(".md")).write_text(answer or "", encoding="utf-8")
    if transcript:
        (base.with_suffix(".json")).write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(base)


def main():
    parser = argparse.ArgumentParser(description="AutoGen DeepSearch multi-agent CLI")
    parser.add_argument("question", type=str, help="Research question to investigate")
    parser.add_argument("--model", type=str, default=None, help="LLM model name (optional)")
    parser.add_argument("--rounds", type=int, default=12, help="Max dialogue rounds")
    parser.add_argument("--full", action="store_true", help="Save full transcript to JSON as well")
    parser.add_argument("--out", type=str, default="others/deepsearch_autogen/output", help="Output directory")

    args = parser.parse_args()
    result = run_deepsearch(args.question, model=args.model, max_rounds=args.rounds, summary_only=not args.full)
    answer = result.get("answer") or "(No final answer produced)"
    transcript = result.get("transcript")
    base = save_output(Path(args.out), args.question, answer, transcript)
    print(f"Saved: {base}.md")
    if transcript:
        print(f"Saved: {base}.json")


if __name__ == "__main__":
    main()


