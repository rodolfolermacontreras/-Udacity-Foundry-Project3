"""
LLM-as-Judge Evaluation Harness for Travel Concierge Agent
Evaluates agent responses against quality criteria and produces numerical scores.
"""

import csv
import json
import asyncio
from datetime import datetime
from app.main import run_request
from pydantic import ValidationError

# Define test scenarios
TEST_CASES = [
    {
        "name": "Test 1: Paris Trip with BankGold",
        "input": {
            "destination": "Paris",
            "travel_dates": "2026-06-01 to 2026-06-08",
            "card": "BankGold"
        },
        "query": "I want to go to Paris from 2026-06-01 to 2026-06-08 with my BankGold card"
    },
    {
        "name": "Test 2: Tokyo Trip with BankPlatinum",
        "input": {
            "destination": "Tokyo",
            "travel_dates": "2026-07-10 to 2026-07-17",
            "card": "BankPlatinum"
        },
        "query": "Plan a trip to Tokyo from July 10-17, 2026. I have a BankPlatinum card"
    },
    {
        "name": "Test 3: Barcelona Trip with BankRewards",
        "input": {
            "destination": "Barcelona",
            "travel_dates": "2026-08-15 to 2026-08-22",
            "card": "BankRewards"
        },
        "query": "I want to visit Barcelona from August 15-22, 2026 with my BankRewards card"
    }
]

# Evaluation criteria with weights
EVALUATION_CRITERIA = {
    "accuracy": {"weight": 0.25, "description": "Accuracy of information provided"},
    "completeness": {"weight": 0.20, "description": "Response completeness"},
    "relevance": {"weight": 0.20, "description": "Relevance to user query"},
    "tool_usage": {"weight": 0.15, "description": "Appropriate tool usage"},
    "structure": {"weight": 0.10, "description": "Response structure"},
    "citations": {"weight": 0.10, "description": "Proper citations"}
}


def evaluate(case: dict) -> dict:
    """
    Evaluate a test case by running the agent and scoring the output.
    
    Args:
        case: Test case dictionary with input parameters and query
        
    Returns:
        Dictionary with evaluation results and numerical scores
    """
    print(f"\n{'='*60}")
    print(f"Evaluating: {case['name']}")
    print(f"{'='*60}")
    
    try:
        # Run the agent with the test query
        query = case.get("query", f"Plan a trip to {case['input']['destination']}")
        print(f"Query: {query}")
        
        result = asyncio.run(run_request(query))
        
        # Parse the JSON response
        try:
            response_data = json.loads(result)
            plan = response_data.get("plan", {})
            valid_json = True
            print("[OK] Valid JSON response")
        except json.JSONDecodeError:
            plan = {}
            valid_json = False
            print("[FAIL] Invalid JSON response")
        
        # Score individual criteria (0-5 scale)
        scores = {}
        
        # 1. Accuracy (check if destination matches)
        destination_match = plan.get("destination", "").lower() == case["input"]["destination"].lower()
        has_weather = plan.get("weather") is not None
        has_currency = plan.get("currency_info") is not None
        scores["accuracy"] = 5.0 if (destination_match and has_weather and has_currency) else (3.0 if destination_match else 1.0)
        
        # 2. Completeness (check required fields)
        required_fields = ["destination", "weather", "card_recommendation", "currency_info", "next_steps"]
        fields_present = sum(1 for f in required_fields if plan.get(f) is not None)
        scores["completeness"] = (fields_present / len(required_fields)) * 5.0
        
        # 3. Relevance (check if card mentioned matches)
        card_rec = plan.get("card_recommendation", {})
        card_mentioned = case["input"]["card"].lower() in str(card_rec).lower()
        scores["relevance"] = 5.0 if card_mentioned else 2.0
        
        # 4. Tool usage (check search results and weather)
        search_results = plan.get("search_results", [])
        has_search = len(search_results) > 0 if isinstance(search_results, list) else search_results is not None
        scores["tool_usage"] = 5.0 if (has_weather and has_search) else (3.0 if has_weather else 1.0)
        
        # 5. Structure (check JSON structure)
        scores["structure"] = 5.0 if valid_json else 0.0
        
        # 6. Citations (check for sources)
        citations = plan.get("citations", [])
        has_citations = len(citations) > 0 if isinstance(citations, list) else citations is not None
        scores["citations"] = 5.0 if has_citations else 0.0
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[criterion] * EVALUATION_CRITERIA[criterion]["weight"]
            for criterion in scores
        )
        
        # Determine pass/fail (threshold: 3.0)
        passed = overall_score >= 3.0
        
        # Print detailed scores
        print(f"\n--- Criterion Scores (0-5 scale) ---")
        for criterion, score in scores.items():
            weight = EVALUATION_CRITERIA[criterion]["weight"] * 100
            print(f"  {criterion}: {score:.1f} (weight: {weight:.0f}%)")
        
        print(f"\n--- Overall Results ---")
        print(f"  Overall Score: {overall_score:.2f}/5.00")
        print(f"  Status: {'PASSED' if passed else 'FAILED'}")
        
        return {
            "valid_json": valid_json,
            "has_citations": has_citations,
            "card_mentioned": card_mentioned,
            "scores": scores,
            "overall_score": overall_score,
            "passed": passed
        }
        
    except Exception as e:
        print(f"[FAIL] Evaluation error: {e}")
        return {
            "valid_json": False,
            "has_citations": False,
            "card_mentioned": False,
            "scores": {k: 0.0 for k in EVALUATION_CRITERIA},
            "overall_score": 0.0,
            "passed": False,
            "error": str(e)
        }


def main():
    """
    Main evaluation function that runs all test cases and produces numerical scores.
    """
    print("\n" + "="*70)
    print("LLM-AS-JUDGE EVALUATION HARNESS")
    print("Travel Concierge Agent - Performance Evaluation")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    total_score = 0.0
    passed_count = 0
    
    # Run all test cases
    for case in TEST_CASES:
        outcome = evaluate(case)
        results.append({
            "test_name": case["name"],
            "destination": case["input"]["destination"],
            **outcome
        })
        total_score += outcome["overall_score"]
        if outcome["passed"]:
            passed_count += 1
    
    # Calculate aggregate metrics
    avg_score = total_score / len(TEST_CASES) if TEST_CASES else 0.0
    pass_rate = (passed_count / len(TEST_CASES)) * 100 if TEST_CASES else 0.0
    
    # Print summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(f"Total Test Cases: {len(TEST_CASES)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(TEST_CASES) - passed_count}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"\n*** AVERAGE SCORE: {avg_score:.2f}/5.00 ***")
    print("="*70)
    
    # Detailed breakdown by criterion
    print("\nCRITERION BREAKDOWN (averaged across all tests):")
    print("-"*50)
    for criterion in EVALUATION_CRITERIA:
        criterion_scores = [r["scores"].get(criterion, 0) for r in results if "scores" in r]
        avg_criterion = sum(criterion_scores) / len(criterion_scores) if criterion_scores else 0
        weight = EVALUATION_CRITERIA[criterion]["weight"] * 100
        print(f"  {criterion:15s}: {avg_criterion:.2f}/5.00 (weight: {weight:.0f}%)")
    
    # Write results to CSV
    csv_path = "app/eval/results.csv"
    try:
        with open(csv_path, "w", newline="") as f:
            fieldnames = ["test_name", "destination", "valid_json", "has_citations", 
                         "card_mentioned", "overall_score", "passed"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved to: {csv_path}")
    except Exception as e:
        print(f"\nWarning: Could not save CSV: {e}")
    
    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)
    
    return avg_score, pass_rate


if __name__ == "__main__":
    main()
