import { BatteryWarning, Flame, Gauge } from "lucide-react";

const ZONE_STYLES = {
  LOW: {
    icon: BatteryWarning,
    accent: "text-sky-100",
    bar: "bg-sky-300",
    badge: "bg-sky-300/12 text-sky-100 ring-sky-300/25",
  },
  MEDIUM: {
    icon: Gauge,
    accent: "text-emerald-100",
    bar: "bg-emerald-300",
    badge: "bg-emerald-300/12 text-emerald-100 ring-emerald-300/25",
  },
  HIGH: {
    icon: Flame,
    accent: "text-amber-100",
    bar: "bg-amber-300",
    badge: "bg-amber-300/12 text-amber-100 ring-amber-300/25",
  },
};

export default function ZoneCards({ zones = [] }) {
  return (
    <section className="grid gap-5 md:grid-cols-3">
      {zones.map((zone) => {
        const style = ZONE_STYLES[zone.zone_id] || ZONE_STYLES.MEDIUM;
        const Icon = style.icon;
        const disabled = zone.status === "DISABLED";

        return (
          <article key={zone.zone_id} className={`control-panel rounded-lg p-5 ${disabled ? "opacity-60" : ""}`}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-400">Balanced zone usage</p>
                <h2 className={`mt-1 text-xl font-semibold ${style.accent}`}>{zone.zone_name}</h2>
              </div>
              <div className={`flex h-10 w-10 items-center justify-center rounded-md bg-slate-900 ${style.accent}`}>
                <Icon className="h-5 w-5" />
              </div>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs uppercase text-slate-500">Available tonnes</p>
                <p className="mt-1 text-3xl font-bold text-white">{Number(zone.available_mass_tonnes || 0).toFixed(1)}t</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Average CV</p>
                <p className="mt-1 text-3xl font-bold text-white">{Number(zone.avg_cv || 0).toFixed(1)}</p>
              </div>
            </div>

            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>Fill percent: {Number(zone.fill_percent || 0).toFixed(0)}%</span>
                <span className={`rounded-full px-2 py-1 font-semibold ring-1 ${style.badge}`}>Status: {zone.status}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className={`h-2 rounded-full ${style.bar}`}
                  style={{ width: `${Math.min(Number(zone.fill_percent || zone.percentage_of_total_mass || 0), 100)}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {Number(zone.percentage_of_total_mass || 0).toFixed(1)}% of available virtual zone mass
              </p>
            </div>

            <p className="mt-4 text-sm leading-6 text-slate-400">{zone.risk_if_overused}</p>
            <p className="mt-3 truncate text-xs text-slate-500">
              Waste codes inside: {zone.waste_codes_inside?.length ? zone.waste_codes_inside.join(", ") : "None"}
            </p>
            <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-500">
              Source note: {zone.source_note}
            </p>
          </article>
        );
      })}
    </section>
  );
}
