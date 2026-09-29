# FitStyle AI — Multi-Agent Fashion Product Discovery & Outfit Recommendation

**FitStyle AI** is a multi-agent fashion recommendation system built for **Thilakawardhana Shopping, Sri Lanka**.

It combines **LLM-based natural-language understanding, hybrid information retrieval, structured SQL filtering, size/variant verification, and deterministic outfit ranking** to help users discover relevant fashion products and build complete outfits from natural-language requests.

> Academic project for **Information Retrieval and Web Analytics (IT3041)**.

---

## ✨ What FitStyle AI Can Do

FitStyle AI supports two main user journeys.

### 1. Product Search

Users can search naturally using constraints such as:

```text
women casual cotton top size M
```

```text
men formal shirt under 5000
```

```text
I want a red dress for women
```

The system understands the request, retrieves relevant products, applies exact structured filters, verifies size availability when requested, and returns valid product results.

### 2. Outfit Recommendation

Users can request a complete outfit using natural language:

```text
I need a smart casual men's outfit for a job interview under 15000.
My shirt size is M and trouser size is 32.
```

The system retrieves and verifies candidates for:

- Top
- Bottom
- Footwear

Then it ranks valid outfit combinations and generates a grounded explanation.

---

# 🧠 Multi-Agent Architecture

FitStyle AI contains **four specialized intelligent agents** coordinated by a central **Coordinator / Orchestrator**.

| Component | Responsibility |
|---|---|
| **Query Understanding Agent** | Converts natural-language fashion requests into structured intent and constraints |
| **Product Retrieval Agent** | Performs BM25 + Qdrant semantic retrieval, Equal RRF fusion, and structured filtering |
| **Size/Fit Agent** | Verifies whether the exact requested product size/variant is currently available |
| **Outfit Recommendation & Explanation Agent** | Ranks valid outfit combinations and generates a grounded explanation |
| **Coordinator / Orchestrator** | Controls the workflow and routes data between agents |

The Coordinator is the orchestration layer and is **not counted as one of the four intelligent agents**.

---

# 🔄 End-to-End System Flow

```text
User
  ↓
React / Vite Frontend
  ↓
Axios HTTP Request
  ↓
FastAPI
  ↓
Request Validation
  ↓
Coordinator / Orchestrator
  ↓
Query Understanding Agent
  ├── Deterministic Parsing
  └── Ollama → Qwen2.5 3B Instruct
  ↓
Intent + Structured Constraints
  ↓
Coordinator Routing
  ↓
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Product Search                  Outfit Recommendation│
│                                                     │
↓                                                     ↓
Product Retrieval Agent              Retrieve Top / Bottom / Shoes
↓                                                     ↓
BM25 + Qdrant Semantic               BM25 + Qdrant Semantic
↓                                                     ↓
Equal RRF                            Equal RRF
↓                                                     ↓
SQL Server Hard Filters              SQL Server Hard Filters
↓                                                     ↓
Availability Check                   Availability + Size Verification
↓                                                     ↓
Size/Fit Agent                       Outfit Recommendation Agent
                                                      ↓
                                              Deterministic Ranking
                                                      ↓
                                               Selected Products
                                                      ↓
                                         Qwen2.5 Explanation
                                                      ↓
                                      Validation / Safe Fallback
└─────────────────────────────────────────────────────┘
                      ↓
                  Coordinator
                      ↓
                 FastAPI Cleanup
                      ↓
                    React UI
```

---

# 🤖 LLM Usage

FitStyle AI uses:

```text
Qwen2.5 3B Instruct
```

Model name:

```text
qwen2.5:3b-instruct
```

The model runs locally through **Ollama**.

> **Qwen2.5 is the LLM. Ollama is the local runtime/model server used to run it.**

The LLM is mainly used in two places:

### Query Understanding
It helps understand flexible natural-language fashion requests and works together with deterministic parsing.

### Grounded Outfit Explanation
After products are already selected and verified, Qwen2.5 generates a natural-language explanation.

The LLM is **not trusted as the source of product facts** such as:

- Product name
- Price
- Size
- Availability
- Target group

Structured product facts are verified from **SQL Server**.

---

# 🔎 Hybrid Information Retrieval

FitStyle AI combines lexical and semantic retrieval.

## BM25
BM25 provides **keyword / lexical matching**.

## Semantic Search
Semantic search uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The model produces **384-dimensional embeddings** for product text.

The vectors are stored and searched in **Qdrant**.

Qdrant collection:

```text
fitstyle_products
```

## Equal Reciprocal Rank Fusion

Results from BM25 and semantic retrieval are combined using:

```text
Equal Reciprocal Rank Fusion (RRF)
```

This combines:

```text
Exact keyword relevance
        +
Semantic meaning
```

---

# 🗄️ SQL Server as the Authoritative Product Source

Microsoft SQL Server stores and verifies structured product data.

It is used for exact constraints such as:

- Category
- Target group
- Material
- Style
- Occasion
- Color
- Maximum price
- Variant availability
- Requested size availability

Core design:

```text
BM25 / Qdrant → Find relevant candidates

SQL Server    → Verify exact facts and hard constraints
```

---

# 📏 Size / Fit Verification

The **Size/Fit Agent** checks `ProductVariants` to verify whether a requested size exists and is currently available.

Example:

```text
requested_size = M
size_available = true
```

This means the requested size exists as an available variant.

It does **not** mean the size is guaranteed to physically fit the user.

---

# 👗 Outfit Recommendation

For outfit requests, the Coordinator retrieves candidates for:

```text
top
bottom
shoes
```

Each role is retrieved through the hybrid retrieval pipeline.

The Outfit Recommendation Agent ranks valid combinations using deterministic criteria such as:

| Factor | Weight |
|---|---:|
| Occasion | 0.30 |
| Style | 0.20 |
| Budget | 0.20 |
| Size | 0.15 |
| Color | 0.10 |
| Availability | 0.05 |

The LLM does **not** select the final products.

---

# 🛡️ Responsible AI & Safety

FitStyle AI includes safeguards to reduce unsupported recommendations and hallucinations.

### Grounded Product Facts
Exact product facts are verified using structured product data.

### No Invented Products
If no valid result satisfies all hard constraints:

```text
no_match
```

is returned instead of inventing a product.

### Clarification Instead of Guessing
Missing/conflicting important information can return:

```text
needs_clarification
```

### Out-of-Domain Detection
Non-fashion requests return:

```text
unsupported_request
```

### LLM Explanation Validation
Generated explanations are validated before being shown.

If an explanation contains unsupported facts, the system can use a deterministic fallback explanation.

### Negation / Exclusion Handling
The system supports constraints such as:

```text
Show me black shoes but not heels
```

```text
I want a red dress, but do not show me blue jeans
```

Negative constraints are separated from the positive retrieval query and enforced before final results are returned.

---

# 📦 Dataset

The project uses a static fashion dataset prepared from **Thilakawardhana Shopping** product data.

| Item | Count |
|---|---:|
| Raw products collected | 1,981 |
| Final clean fashion products | 1,286 |
| Product variants | 5,909 |
| Available variants | 3,099 |

Product IDs:

```text
TH_<product_id>
```

Variant IDs:

```text
THV_<variant_id>
```

---

# 🧹 Data Preparation Pipeline

```text
Raw Product Collection
        ↓
Fashion / Non-Fashion Filtering
        ↓
Manual Review
        ↓
Audit & Cleanup
        ↓
Normalization
        ↓
Fashion Attribute Enrichment
        ↓
Color Extraction
        ↓
Validation
        ↓
Final Product + Variant Datasets
        ↓
SQL Server Import
        ↓
BM25 / Semantic / Qdrant Indexing
```

Validation includes:

- Duplicate product checks
- Orphan variant checks
- Missing price checks
- Availability validation
- Final ID consistency

---

# 📊 Information Retrieval Evaluation

| Retrieval Method | P@10 | R@10 | F1 | NDCG |
|---|---:|---:|---:|---:|
| TF-IDF | 0.2300 | 0.2791 | 0.1560 | 0.3187 |
| BM25 | 0.2650 | 0.3698 | 0.2140 | 0.3924 |
| MiniLM Semantic | 0.1750 | 0.2108 | 0.1260 | 0.2358 |
| Equal RRF Hybrid | 0.2450 | 0.3347 | 0.1981 | 0.3811 |
| BM25 + Hard Filters | 0.5600 | 0.6037 | 0.3866 | **0.9070** |
| Hybrid + Hard Filters | **0.5750** | **0.6167** | **0.4003** | 0.8800 |

---

# ⚙️ Technology Stack

## AI / NLP / Retrieval
- Qwen2.5 3B Instruct
- Ollama
- Sentence Transformers
- `all-MiniLM-L6-v2`
- BM25
- Reciprocal Rank Fusion
- Qdrant

## Backend
- Python
- FastAPI
- Pydantic
- SQL Server
- `pyodbc`

## Frontend
- React
- Vite
- Axios
- Motion
- Lucide React

## Data / Evaluation
- Pandas
- Scikit-learn
- JSON / CSV
- Custom retrieval evaluation scripts

---

# 📁 Project Structure

```text
FitStyle-AI/
│
├── agents/
│   ├── query_understanding_agent.py
│   ├── product_retrieval_agent.py
│   ├── size_fit_agent.py
│   └── outfit_recommendation_agent.py
│
├── api/
│   ├── auth_routes.py
│   └── main.py
│
├── auth/
│   ├── dependencies.py
│   └── security.py
│
├── database/
│   ├── sqlserver_repository.py
│   └── user_repository.py
│
├── orchestrator/
│   └── coordinator.py
│
├── knowledge/
│   ├── fashion_taxonomy.json
│   ├── outfit_rules.json
│   └── size_rules.json
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── qdrant/
│
├── models/
│   ├── bm25/
│   ├── semantic/
│   └── tfidf/
│
├── scripts/
│   ├── bm25/
│   ├── database/
│   ├── hybrid/
│   ├── llm/
│   ├── qdrant/
│   ├── retrieval/
│   ├── semantic/
│   ├── tfidf/
│   └── data-preparation scripts
│
├── evaluation/
│   └── retrieval evaluation outputs
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

# 🚀 Local Setup

## Prerequisites

Install:

- Python 3.x
- Node.js + npm
- Microsoft SQL Server
- SQL Server Management Studio
- ODBC Driver 18 for SQL Server
- Ollama

---

## 1. Clone

```bash
git clone <your-repository-url>
cd FitStyle-Multi-Agentic-AI-System
```

---

## 2. Python Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python packages required by the project environment.

---

## 3. Ollama

```bash
ollama pull qwen2.5:3b-instruct
```

Make sure Ollama is running before starting the backend.

---

## 4. SQL Server

Expected local database:

```text
FitStyleAI
```

Current SQL Server connection configuration uses:

```text
ODBC Driver 18 for SQL Server
SERVER=localhost
DATABASE=FitStyleAI
Trusted_Connection=yes
TrustServerCertificate=yes
```

Use the scripts under:

```text
scripts/database/
```

to import the structured data and test the connection.

---

## 5. Qdrant

Relevant scripts:

```text
scripts/qdrant/create_collection.py
scripts/qdrant/index_products.py
scripts/qdrant/search_qdrant.py
```

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

---

## 6. Retrieval Models

Relevant folders:

```text
scripts/tfidf/
scripts/bm25/
scripts/semantic/
scripts/hybrid/
scripts/retrieval/
```

---

## 7. Start FastAPI

From the project root:

```bash
uvicorn api.main:app --reload
```

Health check:

```text
GET /health
```

Recommendation endpoint:

```text
POST /recommend
```

Example body:

```json
{
  "query": "women casual cotton top size M"
}
```

---

## 8. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Default Vite development URL:

```text
http://localhost:5173
```

---

# 🧪 Example Queries

### Product Search

```text
women casual cotton top size M
```

```text
men formal shirt under 5000
```

```text
I want a red dress for women
```

### Outfit Recommendation

```text
I need a smart casual men's outfit for a job interview under 15000.
```

### Exclusions

```text
Show me black shoes but not heels.
```

```text
Show me blue shirts, but not blue jeans.
```

### Clarification

```text
I need an interview outfit.
```

### Out-of-Domain

```text
Recommend me a laptop.
```

---

# 📡 Response Types

FitStyle AI can return:

```text
success
needs_clarification
no_match
unsupported_request
```

---

# 👥 Team Responsibilities

| Member | Main Responsibility |
|---|---|
| **Member 1** | API, Coordinator, Security, Frontend Integration |
| **Member 2** | Query Understanding, LLM Integration, Fashion Enrichment |
| **Member 3** | Data, SQL Server, Qdrant, Hybrid Retrieval, Evaluation |
| **Member 4** | Size Verification, Outfit Recommendation |

---

# ⚠️ Current Dataset Limitation

Color coverage is much lower than several other enriched attributes.

```text
Products with extracted color: 227 / 1,286
```

Therefore, a strict query such as:

```text
red dress
```

may return fewer results or `no_match` even when visually red products exist but their color is not represented in the structured data.

The system treats this as a **data-quality limitation** rather than silently inventing or relaxing an explicit constraint.

---

# 🔐 Repository Hygiene

Do not commit:

```text
.env
.venv/
__pycache__/
*.pyc
frontend/node_modules/
```

Local Qdrant persistence under:

```text
data/qdrant/
```

should normally remain local unless the team intentionally decides to version generated storage.

---

# 🎯 Key Design Principle

FitStyle AI is **not just an LLM wrapper**.

It combines:

```text
Natural-Language Understanding
        +
Lexical Information Retrieval
        +
Semantic Information Retrieval
        +
Structured Database Filtering
        +
Variant / Size Verification
        +
Deterministic Outfit Ranking
        +
Grounded LLM Explanation
```

---

# 📚 Academic Context

This project was developed for **Information Retrieval and Web Analytics (IT3041)** under the assignment:

> **Design and Implementation of an Agentic AI System Integrating LLMs, NLP, Security, and Information Retrieval**

The system demonstrates:

- Multi-agent behavior
- LLM integration
- NLP
- Information Retrieval
- Security-oriented design
- Coordinated agent communication
- Responsible AI practices
- Retrieval evaluation

---

## License

This repository was developed as an academic project. Add an appropriate license if the project is later released for public reuse.

---

<p align="center">
  <strong>FitStyle AI</strong><br>
  Intelligent Fashion Discovery with Multi-Agent AI
</p>
