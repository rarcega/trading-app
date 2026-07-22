import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Iniciando Trading App Web...")
    print("Accede en: http://localhost:8000")
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
