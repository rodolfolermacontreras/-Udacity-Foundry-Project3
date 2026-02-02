# Output Logs for Udacity Project 3 Submission

## Generated: 2026-02-02

This folder contains output logs from the Travel Concierge Agent system checks and evaluations.

## Files

### 1. system_check_output.txt
Health check results verifying all system components:
- **Result**: 8/8 checks passed
- Checks: Environment Variables, Azure OpenAI, Cosmos DB, Tools, Grounding Search, State Management, Memory Systems, Knowledge Base

### 2. pytest_output.txt
Unit test results:
- **Result**: 76/76 tests passed
- Tests cover: models, state, memory, tools, memory integration

### 3. llm_judge_output.txt
LLM-as-Judge evaluation results:
- **Result**: 3/3 test cases passed
- **Average Score**: 3.63/5.00
- **Pass Rate**: 100%

Criterion breakdown (averaged):
| Criterion | Score | Weight |
|-----------|-------|--------|
| accuracy | 2.33/5.00 | 25% |
| completeness | 5.00/5.00 | 20% |
| relevance | 3.00/5.00 | 20% |
| tool_usage | 3.00/5.00 | 15% |
| structure | 5.00/5.00 | 10% |
| citations | 5.00/5.00 | 10% |

### 4. rag_ingest_output.txt
RAG knowledge base ingestion results:
- **Result**: 7 documents ingested into Cosmos DB
- Documents include card benefits, lounge rules, and travel policies

## Azure Resources Used

| Resource | Name |
|----------|------|
| Azure AI Services | udacity-travel-aoai |
| Cosmos DB | udacity-travel-db-410 |
| AI Foundry Project | udacity-travel-aoai-project |
| Bing Grounding | udacity-travel-bing-grounding |
| AI Agent | Travel Concierge Agent |

## Notes

- All emojis have been removed from code per project rules
- System uses Semantic Kernel 1.36.1 for AI orchestration
- Web search uses Azure AI Foundry Agent with Bing Grounding
