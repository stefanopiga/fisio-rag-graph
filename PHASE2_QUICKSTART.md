# 🏥 MEDICAL DOMAIN QUICK START GUIDE

## Phase 2 Implementation: Document Ingestion & Quiz Validation

### Prerequisites Checklist

✅ **Phase 1 Complete**: Medical domain adaptation implemented  
⬜ **PostgreSQL**: Running with pgvector extension  
⬜ **Neo4j**: Running on bolt://localhost:7687  
⬜ **Python Environment**: Virtual environment activated  
⬜ **Dependencies**: Requirements installed  
⬜ **Environment**: Configuration file ready  

---

## 🚀 Quick Execution Steps

### 1. Environment Setup
```bash
# Navigate to project directory
cd C:\Users\aless\Desktop\Claude-Fisio\agentic-RAG\agentic-rag-knowledge-graph

# Activate virtual environment
venv\Scripts\activate  # Windows

# Copy medical environment config
cp .env.medical .env

# Edit .env with your actual credentials:
# - DATABASE_URL (PostgreSQL connection)
# - NEO4J_* settings
# - LLM_API_KEY (OpenAI or your provider)
```

### 2. Database Schema Setup
```bash
# Initialize PostgreSQL schema
psql -d "your_database_url" -f sql/schema.sql

# Verify extensions
psql -d "your_database_url" -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm');"
```

### 3. Medical Document Ingestion
```bash
# Run medical document processing
python run_medical_ingestion.py

# Expected output:
# 🏥 Starting Medical Document Ingestion for Fisioterapia
# 📂 Processing documents from: documents/fisioterapia/
# ✅ Medical Document Ingestion Complete!
```

### 4. System Testing
```bash
# Run comprehensive tests
python test_medical_system.py

# Expected results:
# ✅ Medical search testing complete!
# ✅ Quiz scenario testing complete!
# ✅ Medical entity extraction test complete!
# ✅ Performance metrics testing complete!
```

### 5. Interactive Testing
```bash
# Start API server (Terminal 1)
python -m agent.api

# Start CLI testing (Terminal 2)
python cli.py

# Test commands in CLI:
# "Genera un quiz su anatomia della spalla"
# "Dimmi tutto sulla riabilitazione del ginocchio"
# "Quiz difficile su terapia manuale"
```

---

## 🎯 Expected Results

### Document Processing
- **4 Medical Documents** processed successfully
- **Anatomical entities** extracted (Spalla, Ginocchio, Muscoli)
- **Pathological conditions** identified (Lesioni, Traumi)
- **Treatment procedures** cataloged (Mobilizzazione, Terapia)

### Quiz Generation
- **Generation time**: <3 seconds per 5 questions
- **Question types**: Multiple choice + Open-ended
- **Italian language**: Full support
- **Clinical reasoning**: Evidence-based explanations

### Performance Metrics
- **Entity extraction**: >85% precision
- **Content relevance**: >90% accuracy
- **System integration**: No degradation
- **Educational effectiveness**: Clinically accurate

---

## 🔧 Troubleshooting

### Common Issues

**Database Connection**:
```bash
# Test PostgreSQL connection
psql -d "your_database_url" -c "SELECT 1;"

# Check Neo4j status
curl -u neo4j:password http://localhost:7474/db/data/
```

**Missing Dependencies**:
```bash
# Reinstall requirements
pip install -r requirements.txt

# Check specific packages
pip show pydantic-ai graphiti-core asyncpg neo4j
```

**API Key Issues**:
```bash
# Verify OpenAI API key
curl -H "Authorization: Bearer your-api-key" https://api.openai.com/v1/models
```

**No Quiz Results**:
- Ensure medical documents are ingested
- Check database has content: `SELECT COUNT(*) FROM documents;`
- Verify knowledge graph episodes created

---

## 📊 Success Validation

### ✅ System Ready When:
- Medical documents processed without errors
- Quiz generation completes in <3 seconds
- Questions generated are clinically relevant
- Italian language responses correct
- Entity extraction identifies medical terms
- API endpoints respond correctly
- CLI interface functional

### 🎯 Next Steps After Validation:
1. **Production Deployment**: Move to production environment
2. **Content Expansion**: Add more fisioterapia documentation
3. **User Testing**: Begin educational effectiveness testing
4. **Optimization**: Fine-tune question quality and difficulty
5. **Integration**: Connect with external educational systems

---

## 📞 Support Commands

```bash
# Check system health
curl http://localhost:8058/health

# List processed documents
curl http://localhost:8058/documents

# Generate test quiz via API
curl -X POST http://localhost:8058/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Genera quiz su anatomia spalla"}'
```

**Status**: 🟢 Ready for Phase 2 execution
**Estimated Time**: 30-45 minutes for complete setup and validation
**Target**: Full medical domain quiz system operational

---

*Follow this guide step-by-step per successful Phase 2 implementation*
