import subprocess
import sys

def start_fastapi():
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"])

def start_streamlit():
    return subprocess.Popen(["streamlit", "run", "frontend/app.py"])

if __name__ == "__main__":
    fastapi_proc = start_fastapi()
    streamlit_proc = start_streamlit()

    fastapi_proc.wait()
    streamlit_proc.wait()
