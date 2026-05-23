import { Play, TriangleAlert } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { simulateMix } from "../api";

function depletionTone(value) {
  if (value >= 0.8) return "text-red-100";
  if (value >= 0.5) return "text-amber-100";
  return "text-emerald-100";
}

function initialMix(cells, optimizedMix) {
  const active = cells.filter((cell) => Number(cell.available_mass_tonnes) > 0);
  if (optimizedMix && Object.keys(optimizedMix).length) return optimizedMix;
  if (!active.length) return {};
  const pct = Math.floor(100 / active.length);
  const mix = Object.fromEntries(active.map((cell) => [cell.waste_code, pct]));
  mix[active[0].waste_code] += 100 - Object.values(mix).reduce((sum, value) => sum + value, 0);
  return mix;
}

export default function SimulatorPanel({ cells = [], defaultSimulation, optimizedMix = {} }) {
  const [mix, setMix] = useState(() => initialMix(cells, optimizedMix));
  const [feedRate, setFeedRate] = useState(10);
  const [duration, setDuration] = useState(2);
  const [result, setResult] = useState(defaultSimulation);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMix(initialMix(cells, optimizedMix));
    setResult(defaultSimulation);
  }, [cells, defaultSimulation, optimizedMix]);

  const activeCells = cells.filter((cell) => Number(cell.available_mass_tonnes) > 0);
  const totalPct = useMemo(
    () => Object.values(mix).reduce((sum, value) => sum + Number(value || 0), 0),
    [mix]
  );

  function updateMix(code, value) {
    setMix((current) => ({ ...current, [code]: Number(value) }));
  }

  async function runSimulation() {
    setError("");
    if (Math.abs(totalPct - 100) > 0.001) {
      setError("Percentages must sum to 100 before simulation.");
      return;
    }

    setLoading(true);
    try {
      const response = await simulateMix({
        mix_percentages: mix,
        feed_rate_tonnes_per_hour: feedRate,
        duration_hours: duration,
      });
      setResult(response.simulation);
    } catch (err) {
      setError(err.message || "Simulation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="control-panel rounded-lg p-5">
      <div className="mb-4">
        <p className="text-sm font-medium text-slate-400">Manual Simulator</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Real-time bunker mix simulation</h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {activeCells.map((cell) => (
          <label key={cell.waste_code} className="block">
            <span className="text-xs uppercase text-slate-500">{cell.waste_code} %</span>
            <input
              type="number"
              min="0"
              max="100"
              value={mix[cell.waste_code] ?? 0}
              onChange={(event) => updateMix(cell.waste_code, event.target.value)}
              className="mt-2 h-10 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-slate-100 outline-none ring-cyan-300/30 focus:ring-2"
            />
          </label>
        ))}
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="text-xs uppercase text-slate-500">Feed rate t/h</span>
          <input
            type="number"
            min="1"
            value={feedRate}
            onChange={(event) => setFeedRate(Number(event.target.value))}
            className="mt-2 h-11 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-slate-100 outline-none ring-cyan-300/30 focus:ring-2"
          />
        </label>
        <label className="block">
          <span className="text-xs uppercase text-slate-500">Duration hours</span>
          <input
            type="number"
            min="0.5"
            step="0.5"
            value={duration}
            onChange={(event) => setDuration(Number(event.target.value))}
            className="mt-2 h-11 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-slate-100 outline-none ring-cyan-300/30 focus:ring-2"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className={`text-sm ${Math.abs(totalPct - 100) < 0.001 ? "text-emerald-100" : "text-amber-100"}`}>
          Current sum: {totalPct}%
        </p>
        <button
          onClick={runSimulation}
          disabled={loading}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-cyan-300 px-4 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:opacity-60"
        >
          <Play className="h-4 w-4" />
          {loading ? "Simulating" : "Simulate Mix"}
        </button>
      </div>

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-300/30 bg-amber-300/10 p-3 text-sm text-amber-100">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <section className="mt-5 rounded-md border border-slate-700/80 bg-slate-950/50 p-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase text-slate-500">Simulated CV</p>
              <p className="mt-1 text-2xl font-bold text-white">{result.blended_cv} MJ/kg</p>
            </div>
            <div>
              <p className="text-xs uppercase text-slate-500">Target band error</p>
              <p className="mt-1 text-2xl font-bold text-white">{result.target_band_error}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-slate-500">Status</p>
              <p className={`mt-1 text-lg font-bold ${result.is_cv_safe && result.is_feasible ? "text-emerald-100" : "text-red-100"}`}>
                {result.is_target_band ? "Target achieved" : result.is_cv_safe ? "Safe" : "Needs review"}
              </p>
            </div>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.keys(result.input_mix_percentages || {}).map((code) => (
              <div key={code} className="rounded-md bg-slate-900/70 p-3">
                <p className="text-xs uppercase text-slate-500">{code} depletion</p>
                <p className={`mt-1 text-lg font-semibold ${depletionTone(result.exhaustion_risk_by_bunker?.[code] || 0)}`}>
                  {Math.round((result.exhaustion_risk_by_bunker?.[code] || 0) * 100)}%
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  {result.consumed_by_bunker?.[code] ?? 0}t consumed, {result.projected_fill_after_2h?.[code] ?? 0}% fill after 2h
                </p>
              </div>
            ))}
          </div>
          {result.infeasible_reasons?.length > 0 && (
            <p className="mt-4 text-sm text-red-100">{result.infeasible_reasons.join(" ")}</p>
          )}
        </section>
      )}
    </article>
  );
}
