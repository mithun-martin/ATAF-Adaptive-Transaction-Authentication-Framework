"""Convenience script to start the backend server."""
import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  ATAF — Simulated Banking Environment")
    print("  API:  http://127.0.0.1:8000")
    print("  Docs: http://127.0.0.1:8000/docs")
    print("  DB:   SQLite (banking.db — auto-created)")
    print("=" * 60 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
