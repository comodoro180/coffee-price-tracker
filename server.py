from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import subprocess
import uvicorn
import json

async def sync(request):
    query = request.query_params.get("q", "cafe buendia")
    print(f"Iniciando búsqueda dinámica para: {query}")
    
    try:
        # Execute the scraper and capture its JSON output
        result = subprocess.run(
            ["python", "scraper.py", query],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"  # Avoid decoding errors
        )
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        
        # Extract progress updates from stderr
        progress_updates = []
        for line in stderr.split("\n"):
            if line.startswith("PROGRESS:"):
                try:
                    progress_json = line.replace("PROGRESS:", "").strip()
                    progress_updates.append(json.loads(progress_json))
                except:
                    pass
        
        if result.returncode == 0 and stdout.strip():
            # The last line of stdout should be our JSON
            lines = stdout.strip().split("\n")
            json_output = lines[-1]
            try:
                data = json.loads(json_output)
                return JSONResponse({
                    "status": "success",
                    "results": data["data"],
                    "timestamp": data["timestamp"],
                    "query": data["search"],
                    "progress": progress_updates  # Include progress updates
                })
            except json.JSONDecodeError:
                return JSONResponse({
                    "status": "error",
                    "message": "Error al procesar JSON del scraper",
                    "details": stdout,
                    "stderr": stderr,
                    "progress": progress_updates
                }, status_code=500)
        else:
            return JSONResponse({
                "status": "error",
                "message": "El scraper falló o no devolvió datos",
                "stderr": stderr,
                "stdout": stdout,
                "progress": progress_updates
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Excepción en el servidor: {str(e)}"
        }, status_code=500)

routes = [
    Route("/sync", endpoint=sync, methods=["GET"])
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"Iniciando servidor en http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
