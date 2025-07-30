"""
Script per analizzare i log strutturati e identificare problemi
"""
import json
from pathlib import Path
from datetime import datetime
import sys
from typing import Dict, List, Any

class LogAnalyzer:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        
    def analyze_backend_logs(self, date: str = None) -> Dict[str, Any]:
        """Analizza i log backend per identificare problemi"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        log_file = self.log_dir / "backend" / f"requests_{date}.jsonl"
        if not log_file.exists():
            return {"error": f"Log file not found: {log_file}"}
        
        analysis = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "errors_by_phase": {},
            "average_phases_per_request": 0,
            "incomplete_requests": [],
            "error_details": []
        }
        
        requests = {}
        
        # Leggi tutti i log
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    request_id = entry.get("request_id")
                    
                    if request_id not in requests:
                        requests[request_id] = {
                            "phases": [],
                            "errors": [],
                            "start_time": entry.get("timestamp"),
                            "has_stream_end": False
                        }
                    
                    requests[request_id]["phases"].append(entry.get("phase"))
                    
                    if entry.get("error"):
                        requests[request_id]["errors"].append(entry)
                        phase = entry.get("phase")
                        analysis["errors_by_phase"][phase] = analysis["errors_by_phase"].get(phase, 0) + 1
                        analysis["error_details"].append({
                            "request_id": request_id,
                            "phase": phase,
                            "error": entry.get("error"),
                            "timestamp": entry.get("timestamp")
                        })
                    
                    if entry.get("phase") == "stream_end":
                        requests[request_id]["has_stream_end"] = True
                        
                except json.JSONDecodeError:
                    continue
        
        # Analizza requests        
        analysis["total_requests"] = len(requests)
        
        for req_id, req_data in requests.items():
            if req_data["errors"]:
                analysis["failed_requests"] += 1
            elif req_data["has_stream_end"]:
                analysis["completed_requests"] += 1
            else:
                analysis["incomplete_requests"].append({
                    "request_id": req_id,
                    "phases": req_data["phases"],
                    "last_phase": req_data["phases"][-1] if req_data["phases"] else None
                })
        
        if requests:
            total_phases = sum(len(r["phases"]) for r in requests.values())
            analysis["average_phases_per_request"] = total_phases / len(requests)
        
        return analysis
    
    def analyze_request_trace(self, request_id: str) -> Dict[str, Any]:
        """Analizza il trace di una specifica richiesta"""
        trace_file = self.log_dir / "debug" / f"trace_{request_id}.json"
        
        if not trace_file.exists():
            return {"error": f"Trace not found for request {request_id}"}
        
        with open(trace_file, "r", encoding="utf-8") as f:
            trace = json.load(f)
        
        analysis = {
            "request_id": request_id,
            "total_phases": len(trace.get("phases", [])),
            "phase_sequence": [p["phase"] for p in trace.get("phases", [])],
            "errors": [p for p in trace.get("phases", []) if p.get("error")],
            "duration": None
        }
        
        # Calcola durata se possibile
        phases = trace.get("phases", [])
        if phases and len(phases) > 1:
            start = datetime.fromisoformat(phases[0]["timestamp"])
            end = datetime.fromisoformat(phases[-1]["timestamp"])
            analysis["duration"] = (end - start).total_seconds()
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Stampa analisi in formato leggibile"""
        print("\n=== LOG ANALYSIS REPORT ===\n")
        
        if "error" in analysis:
            print(f"ERROR: {analysis['error']}")
            return
        
        print(f"Total Requests: {analysis.get('total_requests', 0)}")
        print(f"Completed: {analysis.get('completed_requests', 0)}")
        print(f"Failed: {analysis.get('failed_requests', 0)}")
        print(f"Incomplete: {len(analysis.get('incomplete_requests', []))}")
        print(f"Average Phases per Request: {analysis.get('average_phases_per_request', 0):.1f}")
        
        if analysis.get("errors_by_phase"):
            print("\n--- Errors by Phase ---")
            for phase, count in analysis["errors_by_phase"].items():
                print(f"  {phase}: {count}")
        
        if analysis.get("incomplete_requests"):
            print("\n--- Incomplete Requests ---")
            for req in analysis["incomplete_requests"][:5]:  # Show first 5
                print(f"  Request {req['request_id'][:8]}... stopped at: {req['last_phase']}")
        
        if analysis.get("error_details"):
            print("\n--- Recent Errors ---")
            for error in analysis["error_details"][:5]:  # Show first 5
                print(f"  [{error['timestamp']}] {error['phase']}: {error['error']['type']}")
                print(f"    {error['error']['message']}")

if __name__ == "__main__":
    analyzer = LogAnalyzer()
    
    if len(sys.argv) > 1:
        # Analyze specific request
        request_id = sys.argv[1]
        analysis = analyzer.analyze_request_trace(request_id)
    else:
        # Analyze today's logs
        analysis = analyzer.analyze_backend_logs()
    
    analyzer.print_analysis(analysis)