Contract Intelligence API
This project implements a scalable Contract Intelligence API built on Django Rest Framework (DRF) and Docker. It provides core LLM-powered functionalities including structured data extraction, Retrieval-Augmented Generation (RAG) for question answering, and automated legal risk auditing. A key feature is the Rule Engine Fallback to ensure service continuity when the LLM service is unavailable.
⚙️ Setup and Installation
Follow these steps to get the application running on your local machine using Docker Compose.
1. Prerequisites
•	Docker Desktop: Ensure Docker is installed and running.
•	Git: For cloning the repository.
•	OpenAI API Key: A valid API key with an active billing account (required to prevent 429 Quota errors).
2. Clone and Setup
1.	Clone the repository:
git clone https://github.com/shubhamsharma2961/Contract-Intelligence/  contract-intelligence
cd contract-intelligence
2.	Create the environment file (see Environment Variables section below) and name it .env in the root directory.
3.	Fill the .env file with your credentials.
3. Build and Run Services
Execute the following commands to build the containers and start the application in the background.
Bash
# 1. Build the containers (includes installing dependencies)
docker-compose build

# 2. Start the services (web, db)
docker-compose up -d

# 3. Apply database migrations
docker-compose exec web python manage.py migrate
The API should now be available at http://localhost:8000.
4. Access Documentation
The full API documentation and interactive testing interface are available via Swagger:
•	Swagger UI: http://localhost:8000/docs/
________________________________________
🔑 Environment Variables (.env)
You must create a .env file in the project root with the following variables:
Variable	Description	Example Value
OPENAI_API_KEY	Crucial for LLM features. Your secret key starting with sk-proj-.	sk-proj-XXXXXXXXXXXXXXXXXXXXX
SECRET_KEY	Django's security setting (required).	django-insecure-change-me-later
DEBUG	Set to True for local development.	True
POSTGRES_DB	Name of the database.	contract_db
POSTGRES_USER	Database user.	postgres
POSTGRES_PASSWORD	Database password.	root
POSTGRES_HOST	Database service name (must match docker-compose.yml).	db
________________________________________
⚡ API Endpoints
The API provides seven endpoints across three functional domains: File Management, LLM Intelligence, and System Health.
Method	Endpoint	Description
POST	/api/ingest/	Uploads a PDF file, extracts text, and stores it in the database.
POST	/api/extract/{doc_id}/	LLM. Extracts structured metadata (parties, dates, terms) into JSON.
POST	/api/audit/{doc_id}/	LLM. Identifies and reports specific high-risk clauses in the contract.
POST	/api/ask/	LLM/RAG. Answers a question based only on the content of the specified document.
GET	/api/ask/stream/	LLM/RAG. Streams the RAG answer using Server-Sent Events (SSE).
GET	/api/healthz/	Reports the health status of the database and LLM service.
GET	/docs/	Swagger documentation interface.
________________________________________
📋 Example cURL Commands
These examples assume Document ID 2 has been successfully ingested.
1. Ingest a File
Bash
curl -X POST "http://localhost:8000/api/ingest/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@./path/to/my_contract.pdf"
# Expected Output: {"message": "Ingestion successful", "document_id": 3, "char_count": 29521}
2. Structured Extraction (LLM)
Bash
curl -X POST "http://localhost:8000/api/extract/2/" \
     -H "Content-Type: application/json"
# Expected Output: {"parties": ["MERCY CORPS", "Contractor"], "effective_date": "XXX", ...}
3. RAG Question Answering (LLM)
Bash
curl -X POST "http://localhost:8000/api/ask/" \
     -H "Content-Type: application/json" \
     -d '{"document_id": 2, "question": "What is the notice period for terminating the agreement?"}'
# Expected Output: {"question": "...", "answer": "The notice period for terminating the agreement is 30 days.", "document_id": 2, ...}
4. Risk Audit (LLM)
Bash
curl -X POST "http://localhost:8000/api/audit/2/" \
     -H "Content-Type: application/json"
# Expected Output: [{"clause_name": "Indemnity", "risk_level": "High", "explanation": "...", "evidence_span": "..."}, ...]
________________________________________
⚖️ Architectural Trade-offs
During development, the following trade-offs were made:
Component	Design Choice	Rationale / Trade-off
RAG Implementation	Simple Text Slicing (extracted_text[:20000])	PRO: Avoids the complexity and setup time of a vector database (e.g., Pinecone, ChromaDB). CON: Limits RAG capability to documents that fit within the LLM's context window (up to 16k tokens) and prevents deep semantic search over long documents.
LLM Orchestration	Direct API Calls in utils.py	PRO: Fastest implementation path. CON: Lacks the advanced routing, caching, and observability provided by dedicated LLM frameworks (like LangChain or LlamaIndex).
Data Persistence	Docker Volume for Postgres	PRO: Ensures all documents and metadata persist across container restarts. CON: Requires careful management to avoid accidental deletion of the volume.
Service Reliability	Rule Engine Fallback (FALLBACK_ENABLED)	PRO: Addresses the single point of failure (the LLM). Ensures critical endpoints (/extract, /audit) return a deterministic response instead of a 4XX/5XX error if the LLM service is down or quota is exceeded.
________________________________________
🛑 Rule Engine Fallback
The application includes a mandatory fallback mechanism to maintain service uptime when the LLM is inaccessible (e.g., due to an invalid key or insufficient quota).
How to Toggle
1.	Open api/views.py.
2.	Set the global flag:
Python
# For LLM analysis:
FALLBACK_ENABLED = False 

# For deterministic fallback data:
FALLBACK_ENABLED = True 
3.	Restart the web container after changing the flag: docker-compose restart web.
Demonstration Output (Fallback Enabled)
When the fallback is active, the /extract endpoint will return the pre-programmed deterministic data:
JSON
{
  "parties": ["Fallback Inc.", "Contracting Party"],
  "effective_date": "2025-01-01",
  "message": "Extraction performed using Rule Engine fallback."
}
