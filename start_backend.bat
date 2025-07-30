@echo off
cd /d C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\fisio-rag+graph
call C:\Users\aless\miniconda3\Scripts\activate.bat fisio-rag
set KMP_DUPLICATE_LIB_OK=TRUE
python -m agent.api