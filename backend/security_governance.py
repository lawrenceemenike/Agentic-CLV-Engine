import os
import json
import re
import datetime
import hashlib
import spacy
import mlflow

# Spacy model will be lazy-loaded in the class

class SecurityGovernance:
    def __init__(self):
        # Setup basic logging queue
        self.pending_queue_file = "hitl_pending_queue.json"
        if not os.path.exists(self.pending_queue_file):
            with open(self.pending_queue_file, "w") as f:
                json.dump([], f)
        self.nlp = None
        self._nlp_loaded = False

    def mask_pii(self, text: str) -> str:
        """
        Regex & NER Privacy Masking Ingestion (Epic 3.1)
        """
        masked_text = text
        # Regex masking for emails and phone numbers
        masked_text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', masked_text)
        masked_text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', masked_text)

        # NER masking using Spacy for PERSON and ORG
        if not self._nlp_loaded:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: en_core_web_sm not found. Falling back to regex only if not downloaded yet.")
                self.nlp = None
            self._nlp_loaded = True
            
        if self.nlp:
            doc = self.nlp(masked_text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON"]:
                    masked_text = re.sub(rf'\b{re.escape(ent.text)}\b', f"[REDACTED_CLIENT_NAME_{ent.start}]", masked_text)
                elif ent.label_ in ["ORG"]:
                    masked_text = re.sub(rf'\b{re.escape(ent.text)}\b', f"[REDACTED_ORG_{ent.start}]", masked_text)
        return masked_text

    def apply_deterministic_guardrails(self, account_id: str, baseline_clv: float, final_predicted_clv: float, state_payload: dict, is_tier_1: bool = True) -> dict:
        """
        Deterministic Output Filtering & HITL Gate (Epic 3.2)
        """
        # Hard cap floor
        final_predicted_clv = max(0.0, final_predicted_clv)

        # HITL Shift Check (>30% for Tier 1)
        if baseline_clv > 0:
            shift_percentage = abs(final_predicted_clv - baseline_clv) / baseline_clv
        else:
            shift_percentage = 0.0

        needs_hitl = False
        if is_tier_1 and shift_percentage > 0.30:
            needs_hitl = True
            
            # Queue to HITL
            with open(self.pending_queue_file, "r+") as f:
                queue = json.load(f)
                queue.append({
                    "account_id": account_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "baseline_clv": baseline_clv,
                    "final_predicted_clv": final_predicted_clv,
                    "shift_percentage": shift_percentage,
                    "state_payload": state_payload
                })
                f.seek(0)
                json.dump(queue, f, indent=2)
                f.truncate()
            
            print(f"[SECURITY] HITL trigger activated for {account_id}. Shift: {shift_percentage*100:.2f}%. Paused for manual verification.")

        return {
            "final_predicted_clv": final_predicted_clv,
            "needs_hitl": needs_hitl,
            "shift_percentage": shift_percentage
        }

    def generate_cryptographic_audit_trail(self, account_id: str, state_payload: dict):
        """
        Cryptographic Audit Trail Ledger (Epic 3.3)
        """
        timestamp = datetime.datetime.now().isoformat()
        
        # Serialize state
        state_str = json.dumps(state_payload, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode('utf-8')).hexdigest()

        audit_record = {
            "account_id": account_id,
            "timestamp": timestamp,
            "state_hash": state_hash,
            "payload": state_payload,
            "status": "AUDITED_NIST_RMF"
        }

        filename = f"audit_{account_id}_{timestamp.replace(':', '-')}.json"
        
        with open(filename, "w") as f:
            json.dump(audit_record, f, indent=2)

        # Log into MLflow
        if mlflow.active_run():
            mlflow.log_artifact(filename)
        
        # Keep local copy or cleanup, we'll keep it for visibility
        return filename

if __name__ == "__main__":
    # Test
    sec = SecurityGovernance()
    print(sec.mask_pii("Contact John Doe at john.doe@example.com or 555-123-4567 regarding Acme Corp integration."))
