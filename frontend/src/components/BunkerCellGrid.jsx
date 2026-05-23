import { Archive, Gauge, Truck } from "lucide-react";

function statusTone(status) {
  if (status === "OVER_CAPACITY") return "bg-red-500/12 text-red-100 ring-red-400/25";
  if (status === "NEAR_CAPACITY") return "bg-amber-300/12 text-amber-100 ring-amber-300/25";
  if (status === "EMPTY") return "bg-slate-400/10 text-slate-300 ring-slate-500/25";
  return "bg-emerald-300/12 text-emerald-100 ring-emerald-300/25";
}

function classTone(cvClass) {
  if (cvClass === "LOW") return "text-sky-100";
  if (cvClass === "HIGH") return "text-amber-100";
  return "text-emerald-100";
}

export default function BunkerCellGrid({ cells = [] }) {
  return (
    <section className="mt-5">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">Waste-type bunker cells</p>
          <h2 className="text-xl font-semibold text-white">9 storage bunkers by waste type</h2>
        </div>
        <p className="text-sm text-slate-400">Fill is tracked in tonnes as a volume proxy</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {cells.map((cell) => (
          <article key={cell.waste_code} className="control-panel rounded-lg p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase text-slate-500">{cell.waste_code}</p>
                <h3 className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold text-slate-100">{cell.waste_name}</h3>
              </div>
              <Archive className={`h-5 w-5 shrink-0 ${classTone(cell.cv_class)}`} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs uppercase text-slate-500">Mass</p>
                <p className="mt-1 text-xl font-bold text-white">{Number(cell.available_mass_tonnes).toFixed(1)}t</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">CV</p>
                <p className={`mt-1 text-xl font-bold ${classTone(cell.cv_class)}`}>{Number(cell.cv).toFixed(1)}</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="mb-2 flex justify-between text-xs text-slate-400">
                <span>{Number(cell.fill_pct).toFixed(1)}% full</span>
                <span>{Number(cell.free_capacity_tonnes).toFixed(1)}t free</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className={`h-2 rounded-full ${cell.status === "NEAR_CAPACITY" || cell.status === "OVER_CAPACITY" ? "bg-amber-300" : "bg-cyan-300"}`}
                  style={{ width: `${Math.min(Number(cell.fill_pct), 100)}%` }}
                />
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between gap-2">
              <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${statusTone(cell.status)}`}>
                {cell.status.replaceAll("_", " ")}
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                <Truck className="h-3.5 w-3.5" />
                {Number(cell.projected_incoming_2h_tonnes).toFixed(1)}t / 2h
              </span>
            </div>
            <p className="mt-3 line-clamp-2 text-xs leading-5 text-slate-500">{cell.storage_action}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
