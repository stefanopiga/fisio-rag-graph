import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback
from uuid import uuid4
import asyncio
from contextlib import asynccontextmanager

class StructuredDebugLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Crea sottodirectory
        (self.log_dir / "backend").mkdir(exist_ok=True)
        (self.log_dir / "frontend").mkdir(exist_ok=True)
        (self.log_dir / "debug").mkdir(exist_ok=True)
        
        # Request context storage
        self.current_requests: Dict[str, Dict[str, Any]] = {}
        
    def generate_request_id(self) -> str:
        return str(uuid4())
    
    def log_backend_event(
        self,
        request_id: str,
        phase: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """Log strutturato per eventi backend"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "request_id": request_id,
            "phase": phase,
            "message": message,
            "data": data or {}
        }
        
        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        # Salva in file giornaliero
        date_str = datetime.utcnow().strftime("%Y%m%d")
        log_file = self.log_dir / "backend" / f"requests_{date_str}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # Aggiorna request context
        if request_id not in self.current_requests:
            self.current_requests[request_id] = {
                "start_time": timestamp,
                "phases": []
            }
        
        self.current_requests[request_id]["phases"].append(log_entry)
        
        # Log anche su console per debug immediato
        level = logging.ERROR if error else logging.INFO
        logging.log(level, f"[{phase}] {message}", extra={"request_id": request_id})
    
    def save_request_trace(self, request_id: str):
        """Salva trace completo di una richiesta"""
        if request_id not in self.current_requests:
            return
        
        trace_file = self.log_dir / "debug" / f"trace_{request_id}.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(self.current_requests[request_id], f, indent=2, ensure_ascii=False)
        
        # Cleanup memoria
        del self.current_requests[request_id]
    
    @asynccontextmanager
    async def websocket_request_context(self, websocket_state: str):
        """Context manager per tracciare richieste WebSocket"""
        request_id = self.generate_request_id()
        self.log_backend_event(
            request_id,
            "websocket_start",
            f"WebSocket request initiated, state: {websocket_state}"
        )        
        try:
            yield request_id
        except Exception as e:
            self.log_backend_event(
                request_id,
                "websocket_error",
                "WebSocket request failed",
                error=e
            )
            raise
        finally:
            self.save_request_trace(request_id)
    
    def get_last_request_trace(self) -> Optional[Dict[str, Any]]:
        """Ottieni trace dell'ultima richiesta per debug"""
        trace_files = sorted(
            (self.log_dir / "debug").glob("trace_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if trace_files:
            with open(trace_files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        return None

# Singleton logger instance
debug_logger = StructuredDebugLogger()