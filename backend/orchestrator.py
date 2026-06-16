import json
import re
from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
from backend.security_governance import SecurityGovernance

class GraphState(TypedDict):
    account_id: str
    raw_unstructured_text: str
    quantitative_features: dict
    
    # intermediate
    masked_text: str
    retrieved_contexts: list
    
    # node outputs
    baseline_clv: float
    statistical_variance: list
    qualitative_risk_score: float
    reasoning_summary: str
    tokens_used: int
    
    # final orchestrator output
    final_predicted_clv: float
    is_overridden: bool
    needs_hitl: bool

def node_quant_baseline(state: GraphState) -> dict:
    """
    Epic 2.1: Quantitative Baseline Model Node
    Executes purely mathematical inference.
    We simulate the XGBoost prediction here using the math formula since the live model isn't trained yet.
    """
    features = state['quantitative_features']
    tenure = features.get('tenure_months', 12)
    fee = features.get('monthly_fee', 1000)
    ratio = features.get('user_ratio', 0.5)
    util = features.get('feature_utilization', 0.5)
    tickets = features.get('support_tickets', 0)
    
    # baseline formula
    base_val = (tenure * fee) * (ratio + util)
    base_val = base_val * (1.0 - (tickets * 0.05))
    base_val = max(0, base_val)
    
    return {
        "baseline_clv": float(base_val),
        "statistical_variance": [base_val * 0.9, base_val * 1.1] # mock variance
    }

def node_qualitative_sentiment(state: GraphState) -> dict:
    """
    Epic 2.2: Qualitative Sentiment Context Node
    Uses Ollama 'gemma' to evaluate churn signals.
    """
    masked_text = state['masked_text']
    
    llm = ChatOllama(model="gemma", temperature=0.1)
    
    prompt = f"""
    You are an AI analyzing CRM logs for churn risk.
    Analyze this log: {masked_text}
    Output ONLY a JSON object with 'qualitative_risk_score' (0.0 to 1.0) and 'reasoning_summary' (string).
    """
    
    # Simulate LLM call token usage
    tokens = len(prompt.split()) + 50
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        # Try to parse json from content
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = json.loads(content)
                
            risk_score = float(parsed.get('qualitative_risk_score', 0.5))
            reasoning = parsed.get('reasoning_summary', 'Fallback summary due to parse error.')
        except Exception:
            # Fallback if gemma hallucinates format
            risk_score = 0.8 if 'frustration' in masked_text.lower() or 'resign' in masked_text.lower() else 0.2
            reasoning = "Parsed directly from heuristics due to LLM format failure. " + content[:100]
            
    except Exception as e:
        print(f"[WARN] Gemma Ollama connection failed. Ensure Ollama is running. Error: {e}")
        # Graceful fallback for demonstration if ollama isn't running
        risk_score = 0.8 if 'frustration' in masked_text.lower() or 'resign' in masked_text.lower() else 0.2
        reasoning = "Mocked reasoning due to missing Ollama instance."
        tokens = 0
        
    return {
        "qualitative_risk_score": risk_score,
        "reasoning_summary": reasoning,
        "tokens_used": tokens
    }

def node_orchestrator(state: GraphState) -> dict:
    """
    Epic 2.3: Cognitive Risk Deliberation Orchestrator
    """
    base = state['baseline_clv']
    risk = state['qualitative_risk_score']
    
    is_overridden = False
    final_clv = base
    
    # Threat threshold logic
    if risk > 0.6:
        is_overridden = True
        # Adjust CLV downwards significantly due to high risk
        final_clv = base * (1.0 - risk + 0.2) # e.g., risk 0.8 -> multiply by 0.4
    elif risk < 0.3:
        # positive boost
        final_clv = base * 1.15
        
    # Epic 3 Guardrails
    sec = SecurityGovernance()
    guard_results = sec.apply_deterministic_guardrails(
        account_id=state['account_id'],
        baseline_clv=base,
        final_predicted_clv=final_clv,
        state_payload=state,
        is_tier_1=True
    )
    
    # Log audit
    sec.generate_cryptographic_audit_trail(state['account_id'], state)
    
    return {
        "final_predicted_clv": guard_results['final_predicted_clv'],
        "is_overridden": is_overridden,
        "needs_hitl": guard_results['needs_hitl']
    }

def build_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("quant_node", node_quant_baseline)
    workflow.add_node("sentiment_node", node_qualitative_sentiment)
    workflow.add_node("orchestrator_node", node_orchestrator)
    
    # Parallel execution is simulated by routing start to both, then joining
    # LangGraph natively supports parallel branches if both edges are added from START
    # However, to be simple, we just run them sequentially or use a parallel map.
    # To keep state clean: Start -> Quant -> Sentiment -> Orchestrator
    # (In a true concurrent graph, you'd have a parallel fan-out fan-in, but sequential is fine for this demo)
    
    workflow.add_edge("quant_node", "sentiment_node")
    workflow.add_edge("sentiment_node", "orchestrator_node")
    workflow.add_edge("orchestrator_node", END)
    
    workflow.set_entry_point("quant_node")
    
    return workflow.compile()

if __name__ == "__main__":
    from backend.security_governance import SecurityGovernance
    
    # Initial execution trail
    print("Compiling LangGraph architecture...")
    app = build_graph()
    
    sec = SecurityGovernance()
    raw_text = "CRITICAL CRM LOG: Client John Doe at john.doe@acme.com expressed frustration. Technical champion resigned."
    masked = sec.mask_pii(raw_text)
    
    test_state = {
        "account_id": "ACC-TEST-1",
        "raw_unstructured_text": raw_text,
        "masked_text": masked,
        "quantitative_features": {
            "tenure_months": 24, "monthly_fee": 5000, "user_ratio": 0.8, "feature_utilization": 0.5, "support_tickets": 2
        },
        "retrieved_contexts": [],
        "tokens_used": 0
    }
    
    print("Executing Graph...")
    result = app.invoke(test_state)
    
    print("\n--- GRAPH EXECUTION TRAIL ---")
    print(f"Account: {result['account_id']}")
    print(f"Baseline CLV: ${result['baseline_clv']:.2f}")
    print(f"Qualitative Risk Score: {result['qualitative_risk_score']}")
    print(f"Reasoning: {result['reasoning_summary']}")
    print(f"Final Adjusted CLV: ${result['final_predicted_clv']:.2f}")
    print(f"Overridden: {result['is_overridden']}")
    print(f"HITL Triggered: {result['needs_hitl']}")
    print("-----------------------------\n")
