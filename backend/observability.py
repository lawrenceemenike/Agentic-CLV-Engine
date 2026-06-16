import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision
from datasets import Dataset
import threading

class ObservabilityEngine:
    def __init__(self, experiment_name="Project_Latent_Value_CLV"):
        mlflow.set_experiment(experiment_name)

    def log_quantitative_metrics(self, y_true, y_pred, feature_df: pd.DataFrame, historical_stats: dict = None):
        """
        Quantitative Logging and Feature Drift Alerts (Epic 4.1)
        historical_stats format: {"feature_utilization": {"mean": 0.5, "std": 0.1}, ...}
        """
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        mlflow.log_metric("MAE", mae)
        mlflow.log_metric("R2_Score", r2)

        # Drift detection
        if historical_stats:
            for col, stats in historical_stats.items():
                if col in feature_df.columns:
                    current_mean = feature_df[col].mean()
                    # If mean shifts beyond 1 standard deviation, flag it
                    if abs(current_mean - stats['mean']) > stats['std']:
                        warning_msg = f"DRIFT DETECTED: {col} mean shifted from {stats['mean']} to {current_mean}"
                        print(f"[MLOPS] {warning_msg}")
                        mlflow.set_tag(f"drift_warning_{col}", warning_msg)

    def evaluate_trajectory(self, question, answer, contexts):
        """
        Trajectory Tracing & LLM Judge Evaluation (Epic 4.2)
        Uses Ragas to evaluate faithfulness of the orchestrator/sentiment response.
        """
        def _run_eval():
            # Ragas requires a specific dataset format
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts]
            }
            dataset = Dataset.from_dict(data)
            
            # We try to evaluate, requires LLM setup for ragas, we'll gracefully handle it if tokens are missing
            try:
                result = evaluate(
                    dataset,
                    metrics=[
                        faithfulness,
                        context_precision
                    ]
                )
                print("[LLMOps] Judge Evaluation Metrics:", result)
                
                # Log to mlflow
                if mlflow.active_run():
                    mlflow.log_metric("ragas_faithfulness", result['faithfulness'])
                    mlflow.log_metric("ragas_context_precision", result['context_precision'])
                    
            except Exception as e:
                print(f"[LLMOps] Ragas evaluation skipped/failed: {e}")

        # Offload observability evaluations to a background thread
        thread = threading.Thread(target=_run_eval)
        thread.start()
        return None

    def trace_tokens(self, tokens_used: int, account_id: str):
        """
        Capture end-to-end token consumption
        """
        print(f"[LLMOps] Token Trace for {account_id}: {tokens_used} tokens consumed.")
        if mlflow.active_run():
            mlflow.log_metric(f"tokens_{account_id}", tokens_used)

if __name__ == "__main__":
    obs = ObservabilityEngine()
    print("Observability Engine Initialized.")
