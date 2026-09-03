import subprocess
import sys



FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501


def start_fastapi():
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--reload",
            "--port",
            str(FASTAPI_PORT),
        ]
    )


def start_streamlit():
    return subprocess.Popen(
        [
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            str(STREAMLIT_PORT),
        ]
    )


if __name__ == "__main__":
    fastapi_proc = start_fastapi()
    streamlit_proc = start_streamlit()

    try:
        # Attende la fine dei processi
        fastapi_proc.wait()
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("\nChiusura in corso di FastAPI e Streamlit...")
        # Termina in modo pulito i sottoprocessi quando premi Ctrl+C
        fastapi_proc.terminate()
        streamlit_proc.terminate()

        fastapi_proc.wait()
        streamlit_proc.wait()
        print("Tutti i processi sono stati terminati correttamente.")
