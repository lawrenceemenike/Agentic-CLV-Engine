import { useState } from 'react';
import simulatedData from '../data/clv_simulated_data.json';

const ClvDashboard = () => {
  const [selectedAcc, setSelectedAcc] = useState(simulatedData[0]);

  return (
    <section className="max-w-6xl mx-auto px-6 md:px-8 py-12 bg-[#050505] border border-borderMuted rounded-lg my-12">
      
      {/* Dashboard Meta Header */}
      <div className="border-b border-borderMuted pb-6 mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <span className="font-mono text-[10px] text-accentGold uppercase tracking-widest">[ LIVE OPERATION TERMINAL ]</span>
          <h3 className="font-serif text-2xl text-white mt-1">Project Latent-Value: Core Inference Engine</h3>
        </div>
        {/* Account Selector Tabs */}
        <div className="flex flex-wrap gap-2">
          {simulatedData.map((acc) => (
            <button
              key={acc.id}
              onClick={() => setSelectedAcc(acc)}
              className={`font-mono text-xs px-3 py-1.5 rounded transition-all ${selectedAcc.id === acc.id ? 'bg-white text-black font-medium' : 'bg-[#121212] text-gray-500 border border-borderMuted hover:text-white'}`}
            >
              {acc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Core Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT LAYER (COL SPAN 4): Raw Input Ingestion Streams */}
        <div className="lg:col-span-4 space-y-6">
          <div className="border border-borderMuted p-5 rounded bg-[#0A0A0A]">
            <h4 className="font-mono text-xs text-white uppercase tracking-widest border-b border-borderMuted pb-2 mb-4">1. Ingested Quantitative Metrics</h4>
            <div className="space-y-3 font-mono text-xs text-gray-400">
              <div className="flex justify-between"><span>Contract Tenure:</span><span className="text-white">{selectedAcc.metrics.tenure_months} Months</span></div>
              <div className="flex justify-between"><span>Monthly Contract Value:</span><span className="text-white">${selectedAcc.metrics.monthly_fee}/mo</span></div>
              <div className="flex justify-between"><span>Active Seat Provisioning:</span><span className="text-white">{(selectedAcc.metrics.user_ratio * 100).toFixed(0)}%</span></div>
              <div className="flex justify-between"><span>Advanced Feature Utility:</span><span className="text-white">{(selectedAcc.metrics.feature_utilization * 100).toFixed(0)}%</span></div>
              <div className="flex justify-between"><span>Unresolved Support Escals:</span><span className={`font-bold ${selectedAcc.metrics.support_tickets > 5 ? 'text-red-400' : 'text-emerald-400'}`}>{selectedAcc.metrics.support_tickets} Tickets</span></div>
            </div>
          </div>

          <div className="border border-borderMuted p-5 rounded bg-[#0A0A0A]">
            <h4 className="font-mono text-xs text-white uppercase tracking-widest border-b border-borderMuted pb-2 mb-3">2. Ingested Unstructured Stream</h4>
            <p className="font-sans text-xs text-gray-500 leading-relaxed max-h-[120px] overflow-y-auto">
              "{selectedAcc.unstructured_source}"
            </p>
          </div>
        </div>

        {/* RIGHT LAYER (COL SPAN 8): Agent Calculation and Synthesis Results */}
        <div className="lg:col-span-8 border border-borderMuted p-6 rounded bg-[#0A0A0A] relative overflow-hidden flex flex-col justify-between">
          
          {/* Override Alert Banner */}
          {selectedAcc.agent_outputs.is_overridden && (
            <div className="absolute top-0 right-0 bg-red-950/40 border-b border-l border-red-500/30 text-red-400 font-mono text-[9px] uppercase tracking-widest px-3 py-1">
              [ Cognitive Graph Override Activated ]
            </div>
          )}

          <div>
            <h4 className="font-mono text-xs text-accentGold uppercase tracking-widest mb-6">3. Multi-Agent Reasoning & Synthesis Output</h4>
            
            {/* Metrics Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              <div className="border border-borderMuted p-4 rounded bg-black">
                <span className="font-mono text-[9px] text-gray-500 uppercase tracking-widest block">Quant Base CLV</span>
                <span className="font-serif text-xl text-gray-400 font-bold block mt-1">${selectedAcc.agent_outputs.baseline_clv.toLocaleString()}</span>
              </div>
              <div className="border border-borderMuted p-4 rounded bg-black">
                <span className="font-mono text-[9px] text-gray-500 uppercase tracking-widest block">Context Risk Score</span>
                <span className={`font-mono text-xl font-bold block mt-1 ${selectedAcc.agent_outputs.qualitative_risk_score > 0.4 ? 'text-red-400' : 'text-emerald-400'}`}>{selectedAcc.agent_outputs.qualitative_risk_score}</span>
              </div>
              <div className="border border-borderMuted p-4 rounded bg-black border-l-accentGold/50">
                <span className="font-mono text-[9px] text-accentGold uppercase tracking-widest block">Risk-Adjusted forward CLV</span>
                <span className="font-serif text-xl text-white font-bold block mt-1">${selectedAcc.agent_outputs.final_predicted_clv.toLocaleString()}</span>
              </div>
              <div className="border border-borderMuted p-4 rounded bg-black">
                <span className="font-mono text-[9px] text-gray-500 uppercase tracking-widest block">Dynamic CAC Cap</span>
                <span className="font-serif text-xl text-gray-300 font-bold block mt-1">${selectedAcc.agent_outputs.dynamic_cac_limit.toLocaleString()}</span>
              </div>
            </div>

            {/* Agent Reasoning Output */}
            <div className="border-l-2 border-accentGold pl-4 bg-accentGold/5 p-4 rounded-r">
              <span className="font-mono text-[10px] text-white uppercase tracking-widest block mb-1">Orchestrator Architectural Log</span>
              <p className="font-sans text-sm text-gray-300 leading-relaxed italic">
                "{selectedAcc.agent_outputs.reasoning_summary}"
              </p>
            </div>
          </div>

          {/* Audit & Compliance Signature footer */}
          <div className="border-t border-borderMuted pt-4 mt-6 flex justify-between items-center font-mono text-[9px] text-gray-600 uppercase tracking-widest">
            <span>Governance Class: NIST AI RMF Audit Passed</span>
            <span>Model Version: MLFLOW_REGISTRY_V2.0.4</span>
          </div>

        </div>

      </div>
    </section>
  );
};

export default ClvDashboard;
