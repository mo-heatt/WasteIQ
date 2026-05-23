import { Boxes, CalendarClock, Flame, Hash, ShieldCheck, Target, Warehouse } from "lucide-react";

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "No shipments";
}

function tonnes(value) {
  return `${Number(value || 0).toFixed(1)} t`;
}

export default function BunkerSummary({ dashboard }) {
  const items = [
    { label: "Current bunker CV", value: `${dashboard.current_cv} MJ/kg`, icon: Flame },
    { label: "Target CV: 9.8-10.2 MJ/kg", value: "9.8-10.2 MJ/kg", icon: Target },
    { label: "Safe operating band: 8-12 MJ/kg", value: "8-12 MJ/kg", icon: ShieldCheck },
    { label: "Total mass", value: tonnes(dashboard.total_mass_tonnes), icon: Boxes },
    { label: "Free bunker capacity", value: tonnes(dashboard.storage_summary?.free_capacity_tonnes), icon: Warehouse },
    { label: "Shipment count", value: dashboard.shipment_count, icon: Hash },
    { label: "Latest shipment", value: formatDate(dashboard.latest_timestamp), icon: CalendarClock },
  ];

  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">Current bunker summary</p>
      <h2 className="mt-1 text-xl font-semibold text-white">Target CV: 9.8-10.2 MJ/kg</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex min-h-20 items-center gap-4 rounded-md border border-slate-700/70 bg-slate-950/50 px-4 py-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-800 text-cyan-100">
                <Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs uppercase text-slate-500">{item.label}</p>
                <p className="mt-1 break-words text-lg font-semibold text-slate-100">{item.value}</p>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-4 text-sm text-slate-400">
        Dominant zone: <span className="font-semibold text-slate-100">{dashboard.dominant_zone}</span>. Dominant waste code:{" "}
        <span className="font-semibold text-slate-100">{dashboard.dominant_waste_code}</span>.
      </p>
      <p className="mt-2 text-xs text-slate-500">{dashboard.storage_summary?.capacity_model_note}</p>
    </article>
  );
}
