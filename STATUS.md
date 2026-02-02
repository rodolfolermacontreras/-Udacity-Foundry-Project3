# Project 3: AI Travel Concierge Agent - Status Tracker

## Project Overview

| Field | Details |
|-------|---------|
| **Project Name** | AI Travel Concierge Agent |
| **Course** | Udacity Microsoft Azure AI Foundry Nanodegree |
| **Repository** | https://github.com/rodolfolermacontreras/-Udacity-Foundry-Project3 |
| **Start Date** | January 29, 2026 |
| **Status** | In Progress |

## Technology Stack

- **Orchestration**: Semantic Kernel 1.36.1
- **LLM**: Azure OpenAI (gpt-4.1-mini)
- **Embeddings**: Azure OpenAI (text-embedding-3-small)
- **Vector Database**: Azure Cosmos DB (serverless, West US 2)
- **Data Validation**: Pydantic 2.11.7
- **External APIs**: Open-Meteo (weather), Frankfurter (currency), Azure AI Foundry with Bing Grounding (search)

## Architecture

- **State Machine**: 8-phase workflow (Init, ClarifyRequirements, PlanTools, ExecuteTools, AnalyzeResults, ResolveIssues, ProduceStructuredOutput, Done)
- **Memory**: Short-term (sliding window) + Long-term (Cosmos DB vector store)
- **Tools**: Weather, Currency Exchange, Web Search, Knowledge Base, Trip Card Generation
- **RAG**: Document ingestion with embeddings, vector similarity retrieval

## Test Coverage

| Test Suite | Tests | Status |
|------------|-------|--------|
| test_models.py | Models validation | Passing |
| test_state.py | State machine | Passing |
| test_memory.py | Memory management | Passing |
| test_memory_integration.py | Memory integration | Passing |
| test_tools.py | Tool functions | Passing |
| **Total** | **76 tests** | **All Passing** |

---

## Session Log

### Session 1 - January 29, 2026

**Objective**: Initial project setup and full implementation

**Completed**:
1. Reviewed Project 2 reference materials for patterns and architecture
2. Implemented all core components:
   - `app/state.py` - 8-phase state machine with AgentState class
   - `app/memory.py` - ShortTermMemory with sliding window eviction
   - `app/tools/weather.py` - Open-Meteo API integration
   - `app/tools/fx.py` - Frankfurter currency API
   - `app/tools/search.py` - Azure AI Projects Bing grounding
   - `app/tools/card.py` - Trip card generation
   - `app/tools/knowledge.py` - Knowledge base queries
   - `app/rag/ingest.py` - Document embedding and Cosmos DB upsert
   - `app/rag/retriever.py` - Vector similarity search
   - `app/synthesis.py` - Combines tool results into TripPlan
   - `app/main.py` - Semantic Kernel orchestration
   - `chat.py` - Interactive CLI interface
3. Fixed all test failures (76/76 passing)
4. Removed emojis from all Python files per project rules
5. Updated documentation (README.md, DEVELOPMENT_GUIDE.md, app/README.md)
6. Created `.gitignore` to exclude `.venv/`, `.env`, cache files
7. Initial commit and push to GitHub

**Files Created/Modified**:
- All `app/` modules implemented
- `chat.py` - CLI interface
- `.gitignore` - Git exclusions
- `.env` - Azure credentials (not committed)
- Documentation files updated

**Test Results**: 76/76 passing

**Next Steps**:
1. Configure Azure services with real credentials
2. Set up Cosmos DB collections for RAG and long-term memory
3. Test end-to-end with live Azure services
4. Capture screenshots for Udacity submission

---

### Session 2 - January 31, 2026

**Objective**: Azure resource provisioning and configuration

**Completed**:
1. Verified Azure CLI login and subscription access
2. Reviewed existing Azure OpenAI resource (`udacity-agentic-ai-eastus-resour`)
   - Found existing deployments: gpt-4.1, gpt-4.1-mini
   - Deployed text-embedding-3-small for embeddings
3. Created Cosmos DB account (`udacity-travel-cosmos`) in West US 2
   - Serverless mode with vector search capability enabled
   - Created database: `ragdb`
   - Created container: `snippets` with partition key `/pk`
   - Tested connection with `setup_cosmos.py` script
4. Researched Azure AI Foundry architecture for agents
   - Learned: Bing Search API is retired, replaced by "Grounding with Bing Search"
   - Grounding with Bing requires Azure AI Foundry project + Bing Grounding resource
   - File Search tool in Foundry provides built-in RAG with vector stores
5. Created `setup_azure.py` script for automated resource configuration
6. Generated `.env` file with Azure OpenAI and Cosmos DB credentials

**Azure Resources Created**:
| Resource | Name | Region | Status |
|----------|------|--------|--------|
| Azure OpenAI | udacity-agentic-ai-eastus-resour | East US | Active |
| Cosmos DB | udacity-travel-cosmos | West US 2 | Active |
| Embedding Deployment | text-embedding-3-small | East US | Active |

**Files Created**:
- `app/scripts/setup_azure.py` - Automated Azure setup script
- `app/scripts/setup_cosmos.py` - Cosmos DB test script
- `.env` - Populated with Azure credentials (not committed)

**Removed Temporary Files**:
- `cosmos-index-policy.json` - Temporary config file
- `bing-props.json` - Temporary config file  
- `bing-template.json` - ARM template attempt

**Findings**:
- Bing Search API v7 is retired - cannot create new resources
- Must use "Grounding with Bing Search" resource via Azure portal
- Azure AI Foundry portal required for agent creation with Bing grounding
- Model deployed is gpt-4.1-mini (not gpt-4o-mini as originally planned)

**Next Steps**:
1. Create Azure AI Foundry project via portal (https://ai.azure.com)
2. Create Grounding with Bing Search resource via portal
3. Connect Bing grounding to agent in Foundry portal
4. Update .env with PROJECT_ENDPOINT, AGENT_ID, BING_CONNECTION_ID
5. Test end-to-end functionality
6. Capture screenshots for submission

---

### Session 3 - February 2, 2026

**Objective**: Complete Azure setup using Udacity student account and integrate Bing Grounding

**Completed**:
1. Logged into Azure using Udacity student credentials
   - Account: `student_7pmnza3vml59x3p6_004410128@vocareumvocareum.onmicrosoft.com`
   - Subscription: `Udacity-410` (052d7bab-4db1-4651-a14c-c5b4d14f6cb4)
   - Resource Group: `Regroup_8kkYx8D`
2. Created Azure AI Services resource (`udacity-travel-aoai`) in West US
   - Deployed gpt-4o (GlobalStandard, 10K TPM)
   - Deployed gpt-4o-mini (GlobalStandard, 10K TPM)
   - Deployed text-embedding-3-small (Standard, 10K TPM)
3. Created Cosmos DB account (`udacity-travel-db-410`)
   - Serverless mode with vector search enabled
   - Database: `ragdb`, Container: `snippets`
4. Manually created Bing Grounding resource (`udacity-travel-bing-grounding`) via Azure Portal
5. Manually created AI Foundry project (`udacity-travel-aoai-project`) via Azure AI Foundry Portal
6. Created "Travel Concierge Agent" in AI Foundry with Bing tool connected
   - Agent ID: `asst_NhCbOjFClBRXYD1VSMOnI7hU`
   - Model: gpt-4o
7. Updated `.env` file with corrected endpoint:
   - Changed from `westus.api.cognitive.microsoft.com` to `udacity-travel-aoai.cognitiveservices.azure.com`
8. Rewrote `app/tools/search.py` to integrate AI Foundry Agent with Bing Grounding
   - Uses `azure-ai-projects` SDK with `DefaultAzureCredential`
   - Falls back to mock results if agent unavailable
9. Fixed FX rate display bug in `synthesis.py`
   - Frankfurter API returns converted amount, not rate
   - Now correctly calculates rate as `converted_amount / input_amount`
10. All 76 tests passing

**Azure Resources (Udacity Account - Regroup_8kkYx8D)**:
| Resource | Name | Region | Status |
|----------|------|--------|--------|
| Azure AI Services | udacity-travel-aoai | West US | Active |
| gpt-4o | gpt-4o | West US | Deployed |
| gpt-4o-mini | gpt-4o-mini | West US | Deployed |
| text-embedding-3-small | text-embedding-3-small | West US | Deployed |
| Cosmos DB | udacity-travel-db-410 | West US | Active |
| AI Foundry Project | udacity-travel-aoai-project | West US | Active |
| Bing Grounding | udacity-travel-bing-grounding | Global | Active |
| AI Agent | Travel Concierge Agent | West US | Active |

**Bing Grounding Integration**:
- Successfully integrated via AI Foundry Agent
- Search queries now return real-time web results from Bing
- Example: "best restaurants in Paris" returns current 2026 restaurant recommendations
- Falls back to mock results if Azure CLI not logged in

**Bug Fixes**:
1. FX Rate Display: Changed from showing converted amount (84.46) as rate to actual rate (0.8446)
   - File: `app/synthesis.py` line 263
   - Fix: `rate = converted_amount / input_amount`

**Test Results**:
```
Bing Search: Working (real-time results via AI Foundry Agent)
Weather API: Working (Open-Meteo)
Currency API: Working (Frankfurter, rate calculation fixed)
Azure OpenAI: Working (chat completions confirmed)
Cosmos DB: Working (connection confirmed)
Unit Tests: 76/76 passing
```

**Files Modified**:
- `app/tools/search.py` - Complete rewrite for AI Foundry Agent integration
- `app/synthesis.py` - Fixed FX rate calculation bug
- `tests/test_tools.py` - Updated test for search fallback behavior
- `.env` - Corrected AZURE_OPENAI_ENDPOINT

**Scaffolding Scripts to Delete**:
- `app/scripts/setup_azure.py` - Used for initial resource setup, can be deleted
- `app/scripts/setup_cosmos.py` - Used for Cosmos DB testing, can be deleted

---

### Session 3 Continued - February 2, 2026 (Part 2)

**Objective**: Fix emoji violations, generate output files, prepare for submission

**Completed**:
1. Removed all emojis from Python files (per project rules)
   - Replaced with text tags: `[OK]`, `[ERROR]`, `[WARN]`, `[START]`, `[PHASE]`, etc.
   - Files affected: main.py, ingest.py, retriever.py, llm_judge.py, synthesis.py, and others
2. Generated output files in `outputs/` directory:
   - `system_check_output.txt` - 8/8 checks passed
   - `pytest_output.txt` - 76/76 tests passed
   - `llm_judge_output.txt` - 3.63/5.00 avg score, 100% pass rate
   - `rag_ingest_output.txt` - 7 documents ingested
   - `README.md` - Summary of outputs
3. Verified all tests still pass after emoji removal (76/76)
4. Fixed RAG embedding handling (numpy array issue)
5. Completed judge.py implementation with weighted scoring

**LLM Judge Evaluation Results** (February 2, 2026):
| Criterion | Score | Weight |
|-----------|-------|--------|
| accuracy | 2.33/5.00 | 25% |
| completeness | 5.00/5.00 | 20% |
| relevance | 3.00/5.00 | 20% |
| tool_usage | 3.00/5.00 | 15% |
| structure | 5.00/5.00 | 10% |
| citations | 5.00/5.00 | 10% |
| **Overall** | **3.63/5.00** | 100% pass |

**System Check Results** (February 2, 2026):
- Environment Variables: PASS
- Azure OpenAI: PASS
- Cosmos DB: PASS
- Tools: PASS
- Grounding Search: PASS
- State Management: PASS
- Memory Systems: PASS
- Knowledge Base: PASS
- **Total: 8/8 checks passed**

**Files Modified**:
- All `app/` Python files - Emoji removal
- `outputs/` directory created with output logs

**Next Steps**:
1. Capture Azure Portal screenshots
2. Commit to GitHub
3. Final submission preparation

---

## Pending Tasks

- [x] Azure AI Services resource (gpt-4o, gpt-4o-mini, embeddings)
- [x] Cosmos DB with vector search
- [x] Update .env with credentials
- [x] Test Azure OpenAI connection
- [x] Test Cosmos DB connection
- [x] Bing Grounding via AI Foundry Agent
- [x] Search tool integration with live Bing results
- [x] Fix FX rate display bug
- [x] Implement LLM Judge evaluation harness (judge.py)
- [x] Remove all emojis from code (project rule)
- [x] Generate output files for submission
- [x] Run LLM Judge and capture numerical output (3.63/5.00)
- [x] System check passing (8/8)
- [ ] Configure AI Foundry Agent instructions
- [ ] Capture Azure Portal screenshots
- [ ] Delete scaffolding scripts (setup_azure.py, setup_cosmos.py)
- [ ] Final GitHub commit and submission

## Submission Requirements (Per Rubric)

### Required Screenshots:

| # | Screenshot | Location | Status |
|---|------------|----------|--------|
| 1 | Azure OpenAI Deployments | Azure Portal > Azure OpenAI > Deployments | NEED |
| 2 | Cosmos DB Data Explorer with items | Azure Portal > Cosmos DB > Data Explorer | NEED |
| 3 | Azure AI Studio Bing connection | ai.azure.com > Project > Connections | HAVE |
| 4 | State transitions console output | `outputs/system_check_output.txt` | HAVE |
| 5 | RAG VectorDistance scores | `outputs/rag_ingest_output.txt` | HAVE |
| 6 | LLM Judge numerical score | `outputs/llm_judge_output.txt` | HAVE (3.63/5.00) |

### Screenshot Details:

**1. Azure OpenAI Deployments**
- URL: portal.azure.com > udacity-travel-aoai > Model deployments
- Show: gpt-4o, gpt-4o-mini, text-embedding-3-small all with "Succeeded" status

**2. Cosmos DB Data Explorer**
- URL: portal.azure.com > udacity-travel-db-410 > Data Explorer
- Show: ragdb database, snippets container, at least one stored item with embedding vector

**3. Azure AI Studio Bing Connection (HAVE)**
- URL: ai.azure.com > udacity-travel-aoai-project > Agents
- Show: Travel Concierge Agent with Bing tool connected, "Active" status

**4. State Transitions Console**
- Run: `python chat.py` with a travel query
- Show: Phase transitions (Init -> ClarifyRequirements -> PlanTools -> ExecuteTools -> ... -> Done)

**5. RAG VectorDistance Scores**
- Run: Knowledge retrieval that shows similarity scores
- Show: Query embedding generated, VectorDistance query, results with scores

**6. LLM Judge Numerical Output**
- Run: `python -m app.eval.judge`
- Show: Criterion scores (0-5), overall weighted score, pass/fail status

### AI Foundry Agent Configuration Needed:
The agent at ai.azure.com needs instructions configured:
```
You are a Travel Search Assistant for Banking International's Travel Concierge service.
When given a search query, use your Bing search capability to find relevant travel information.
Return factual, well-sourced information with ratings and prices when available.
```
Temperature: 0.7
Model: gpt-4o

## Notes

- Project follows strict rules: no emojis in code, proper documentation, GitHub tracking
- Virtual environment at `.venv/` (excluded from git)
- Credentials in `.env` file (excluded from git, template in `env.example`)
- Search tool requires Azure CLI login to Udacity account for Bing Grounding
- FX rate bug fixed: now shows 0.8446 instead of 84.46
- LLM Judge implemented with weighted scoring (accuracy, completeness, relevance, tool_usage, structure, citations)

## Big Picture Plan

1. **COMPLETED** - Core implementation (state machine, memory, tools, RAG, synthesis)
2. **COMPLETED** - Unit tests (76/76 passing)
3. **COMPLETED** - Azure OpenAI and Cosmos DB provisioning
4. **COMPLETED** - Azure AI Foundry setup with Bing Grounding
5. **COMPLETED** - Search tool integration with AI Foundry Agent
6. **COMPLETED** - Bug fixes (FX rate display, RAG embeddings)
7. **COMPLETED** - LLM Judge evaluation harness (3.63/5.00 avg)
8. **COMPLETED** - System check (8/8 passing)
9. **COMPLETED** - Emoji removal and output file generation
10. **IN PROGRESS** - Capture Azure Portal screenshots
11. **PENDING** - Delete scaffolding scripts
12. **PENDING** - Final GitHub commit and submission
