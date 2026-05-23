import { CheckCircle2, ClipboardCheck, ShieldCheck } from "lucide-react";
import { useState } from "react";

function sortedMix(mix = {}) {
  return Object.entries(mix)
    .filter(([, pct]) => Number(pct) > 0)
    .sort((a, b) => Number(b[1]) - Number(a[1]));
}

export default function MixRecommendation({ data }) {
  const [approved, setApproved] = useState(false);
  const optimized = data?.optimized_mix || {};
  const simulation = data?.simulation || {};
  const agent = data?.agent || {};
  const mix = sortedMix(optimized.recommended_mix_percentages);
  const safe = optimized.is_safe && optimized.is_within_target_band;

  return (
    <article className="control-panel rounded-lg p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">Recommended corrective mix</p>
          <h2 className="mt-1 text-2xl font-semibold text-white">Real-time waste-type feed plan</h2>
        </div>
        <span className={`inline-flex w-fit rounded-md px-3 py-2 text-sm font-semibold ring-1 ${safe ? "bg-emerald-300/12 text-emerald-100 ring-emerald-300/25" : "bg-amber-300/12 text-amber-100 ring-amber-300/25"}`}>
          {safe ? "TARGET BAND" : "SAFE RANGE"}
        </span>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {mix.slice(0, 6).map(([code, pct]) => (
          <div key={code} className="rounded-md border border-slate-700/80 bg-slate-950/50 p-4">
            <p className="text-xs uppercase text-slate-500">Bunker {code}</p>
            <p className="mt-2 text-4xl font-bold text-cyan-100">{Number(pct).toFixed(0)}%</p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-4">
        <div>
          <p className="text-xs uppercase text-slate-500">Expected blended CV</p>
          <p className="mt-1 text-xl font-semibold text-white">{optimized.expected_cv} MJ/kg</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Preferred target</p>
          <p className="mt-1 text-xl font-semibold text-white">9.8-10.2</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Feed rate</p>
          <p className="mt-1 text-xl font-semibold text-white">{optimized.feed_rate_tonnes_per_hour} t/h</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Duration</p>
          <p className="mt-1 text-xl font-semibold text-white">{optimized.duration_hours} h</p>
        </div>
      </div>

      <div className="mt-5 rounded-md border border-slate-700/80 bg-slate-950/60 p-4">
        <div className="flex items-start gap-3">
          <ClipboardCheck className="mt-0.5 h-5 w-5 shrink-0 text-cyan-200" />
          <div>
            <p className="font-semibold text-slate-100">AI explanation, deterministic calculation</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{agent.summary}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{agent.why_this_mix}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{agent.zone_preservation_reasoning}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2 text-sm text-slate-400">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-200" />
          <span>
            Operator approval required. {agent.safety_note} {agent.confidence}
          </span>
        </div>
        <button
          onClick={() => setApproved(true)}
          disabled={approved}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-bold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-default disabled:bg-emerald-300/60"
        >
          <CheckCircle2 className="h-5 w-5" />
          {approved ? "Approved" : "Approve recommendation"}
        </button>
      </div>

      <div className="mt-5 rounded-md border border-slate-700/80 bg-slate-950/40 p-4">
        <p className="text-sm font-semibold text-slate-100">2-hour bunker depletion simulation</p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {mix.slice(0, 6).map(([code]) => (
            <div key={code}>
              <p className="text-xs uppercase text-slate-500">{code}</p>
              <p className="mt-1 text-sm text-slate-300">
                Consumed {simulation.consumed_by_bunker?.[code] ?? 0}t, remaining {simulation.remaining_by_bunker?.[code] ?? 0}t
              </p>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
