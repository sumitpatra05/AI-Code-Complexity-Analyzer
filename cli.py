"""Usage: python cli.py path/to/file.py [--ai]"""
import sys
from analyzer import analyze_code
from ai_review import ai_review


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = open(sys.argv[1], encoding="utf-8").read()
    r = analyze_code(source)
    if "error" in r:
        sys.exit(r["error"])
    print("SUMMARY")
    for k, v in r["summary"].items():
        print(f"  {k}: {v}")
    print("\nFUNCTIONS")
    for f in r["functions"]:
        print(f"  {f['grade']} {f['name']}:{f['line']}  CC={f['cyclomatic']} "
              f"cog={f['cognitive']} nest={f['max_nesting']}  {f['time_estimate']}")
    print("\nSUGGESTIONS")
    for s in r["suggestions"]:
        print(" -", s)
    if "--ai" in sys.argv:
        print("\nAI REVIEW\n" + ai_review(source, r))


if __name__ == "__main__":
    main()
