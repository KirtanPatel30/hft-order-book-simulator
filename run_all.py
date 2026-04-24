"""run_all.py — Run the full Order Book pipeline."""
import subprocess, sys
from pathlib import Path

def run(cmd, desc):
    print(f"\n{'='*60}\n  {desc}\n{'='*60}")
    r = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent)
    if r.returncode != 0:
        print(f"ERROR: failed with code {r.returncode}")
        sys.exit(r.returncode)

if __name__ == "__main__":
    print("\n⚡ HFT ORDER BOOK SIMULATOR — FULL RUN")
    print("="*60)
    run("python -m pytest tests/ -v",        "STEP 1/2: Unit tests")
    run("python orderbook/engine.py",        "STEP 2/2: Engine validation")
    print("\n✅ COMPLETE!")
    print("  streamlit run dashboard/app.py  → http://localhost:8501")
    print("  uvicorn api.main:app --reload   → http://localhost:8000/docs")
