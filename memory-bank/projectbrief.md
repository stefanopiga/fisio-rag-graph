# Fisio RAG+Graph Project Brief

**Version**: 1.3
**Last Updated**: 2025-07-30

## 1. Project Vision

To create a sophisticated, AI-powered assistant for physiotherapy students and professionals. This tool will leverage a unique combination of Retrieval-Augmented Generation (RAG) and Knowledge Graphs (KG) to provide accurate, context-aware, and dynamically updated information from a specialized knowledge base.

## 2. Core Problem

Physiotherapy knowledge is vast, constantly evolving, and spread across numerous sources (textbooks, research papers, clinical guidelines). Students and practitioners need a tool that can quickly synthesize this information, answer complex queries, and provide evidence-based insights, bridging the gap between theoretical knowledge and clinical practice.

## 3. Key Objectives & Success Metrics

| Objective ID | Description | Key Metrics | Status |
| :--- | :--- | :--- | :--- |
| **OBJ-01** | **Robust Backend API** | - API endpoints for document ingestion, search, and chat are fully functional.<br>- WebSocket handles concurrent connections without failure.<br>- Latency for search queries < 2 seconds.<br>- **NEW**: Comprehensive REST API with 20+ endpoints implemented. | **Completed** |
| **OBJ-02** | **Advanced Search** | - Hybrid search (Vector + Graph) returns more relevant results than single-method searches.<br>- Graph-based queries correctly identify and traverse relationships between concepts.<br>- **NEW**: Search functionality available via both WebSocket and HTTP REST endpoints. | **Completed** |
| **OBJ-03** | **Interactive UI** | - Modern, responsive React UI is fully interactive and bug-free.<br>- Real-time streaming of chat responses via WebSocket is smooth and reliable.<br>- Dynamic sidebars for conversation and document management are implemented. | **Completed** |
| **OBJ-04** | **Scalable Ingestion** | - Pipeline supports ingestion from PDFs, text files, and web URLs.<br>- Knowledge Graph is automatically and accurately updated with new entities and relationships. | **In Progress** |
| **OBJ-05** | **Production Readiness** | - Authentication system with JWT tokens implemented.<br>- All critical bugs resolved (9 major fixes applied).<br>- Complete end-to-end functionality verified with test suite.<br>- WebSocket streaming fully operational.<br>- Advanced debug infrastructure operational.<br>- System stable and production-ready. | **Completed** |
| **OBJ-06** | **Claude Flare Integration** | - Agent decision engine with dynamic orchestration.<br>- Advanced workflow management.<br>- Enhanced RAG with advanced patterns.<br>- Robust testing framework based on vitest. | **Planned** |

## 4. Scope

### Included in scope:
-   **Backend**: FastAPI server with WebSocket support, PostgreSQL with `pgvector`, and Neo4j integration.
-   **AI Agent**: Powered by `pydantic-ai` with hybrid search capabilities.
-   **Frontend**: A fully interactive and modern React (TypeScript) single-page application.
-   **Ingestion**: Initial scripts for processing `pdf` and `txt` files.
-   **Remote Logging**: System to capture frontend console logs for streamlined debugging.

### Out of scope (for this version):
-   Multi-user authentication and role-based access control.
-   Deployment to a production environment.
-   Advanced data visualization for the knowledge graph.

### Planned for Claude Flare Integration:
-   Advanced agent decision engine with dynamic orchestration.
-   Workflow management with structured execution paths.
-   Enhanced RAG with advanced retrieval patterns.
-   Robust testing framework based on vitest.
-   State management with persistent context.

## 5. Target Audience

-   **Primary**: Physiotherapy students.
-   **Secondary**: Licensed physiotherapists, researchers, and educators in the field.

## 6. User Experience Goals

| Metric | Goal | Status |
| :--- | :--- | :--- |
| **Usability** | The interface is intuitive, allowing users to start chatting or searching with minimal guidance. | **Achieved** |
| **Performance** | The application feels fast and responsive, with chat answers streaming in real-time. | **Achieved** |
| **Interactivity** | The UI provides a dynamic and engaging user experience, moving beyond static mockups. | **Achieved** |
| **Reliability** | The system is stable, with effective error handling on both frontend and backend. | **Achieved** |
