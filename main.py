import subprocess
import sys

# --- Configurazione Porte ---
# Definizione delle porte su cui verranno avviati i due servizi
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501


def start_fastapi():
    """Avvia il backend FastAPI utilizzando Uvicorn come server ASGI.

    Usa 'sys.executable' per garantire che venga utilizzato lo stesso
    ambiente virtuale/interprete Python in cui gira questo script.
    """
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",  # Percorso dell'istanza FastAPI (modulo backend.main, variabile app)
            "--reload",  # Attiva il ricaricamento automatico al salvataggio del codice
            "--port",
            str(FASTAPI_PORT),
        ]
    )


def start_streamlit():
    """Avvia l'interfaccia grafica del frontend tramite Streamlit."""
    return subprocess.Popen(
        [
            "streamlit",
            "run",
            "frontend/app.py",  # File entry point della dashboard/interfaccia Streamlit
            "--server.port",
            str(STREAMLIT_PORT),
        ]
    )


if __name__ == "__main__":
    # --- Avvio Servizi ---
    # Esegue entrambi i processi in parallelo come sottoprocessi non bloccanti
    fastapi_proc = start_fastapi()
    streamlit_proc = start_streamlit()

    try:
        # --- Gestione Ciclo di Vita ---
        # Attende indefinitamente che uno dei due processi termini spontaneamente
        fastapi_proc.wait()
        streamlit_proc.wait()
    except KeyboardInterrupt:
        # --- Chiusura Controllata (Graceful Shutdown) ---
        # Intercetta la combinazione di tasti Ctrl+C inviata dall'utente
        print("\nChiusura in corso di FastAPI e Streamlit...")

        # Invia il segnale SIGTERM a ciascun sottoprocesso per arrestarli
        fastapi_proc.terminate()
        streamlit_proc.terminate()

        # Attende che i processi liberino completamente risorse e porte prima di uscire
        fastapi_proc.wait()
        streamlit_proc.wait()

        print("Tutti i processi sono stati terminati correttamente.")