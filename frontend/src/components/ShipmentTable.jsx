function zoneTone(zone) {
  if (zone === "LOW") return "bg-sky-300/12 text-sky-100";
  if (zone === "HIGH") return "bg-amber-300/12 text-amber-100";
  return "bg-emerald-300/12 text-emerald-100";
}

export default function ShipmentTable({ shipments = [] }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">Latest shipments</p>
          <h2 className="text-xl font-semibold text-white">Incoming bunker feed</h2>
        </div>
        <p className="text-sm text-slate-400">Latest 10 rows</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-500">
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Timestamp</th>
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Truck</th>
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Waste code</th>
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Waste name</th>
              <th className="border-b border-slate-700/80 px-3 py-3 text-right font-semibold">Tonnes</th>
              <th className="border-b border-slate-700/80 px-3 py-3 text-right font-semibold">CV</th>
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Bunker</th>
              <th className="border-b border-slate-700/80 px-3 py-3 font-semibold">Assigned zone</th>
            </tr>
          </thead>
          <tbody>
            {shipments.map((shipment) => (
              <tr key={`${shipment.timestamp}-${shipment.truck_id}`} className="text-slate-200">
                <td className="border-b border-slate-800 px-3 py-3 whitespace-nowrap">
                  {shipment.timestamp ? new Date(shipment.timestamp).toLocaleString() : "Unknown"}
                </td>
                <td className="border-b border-slate-800 px-3 py-3 whitespace-nowrap">{shipment.truck_id || "Unknown"}</td>
                <td className="border-b border-slate-800 px-3 py-3">
                  <span className="rounded-md bg-slate-800 px-2 py-1 font-semibold text-cyan-100">{shipment.waste_code || "UNKNOWN"}</span>
                </td>
                <td className="max-w-72 border-b border-slate-800 px-3 py-3 text-slate-300">{shipment.waste_name || "Unknown waste code"}</td>
                <td className="border-b border-slate-800 px-3 py-3 text-right">{Number(shipment.weight_tonnes || 0).toFixed(1)}</td>
                <td className="border-b border-slate-800 px-3 py-3 text-right">{Number(shipment.cv || 0).toFixed(1)}</td>
                <td className="border-b border-slate-800 px-3 py-3">
                  <span className="rounded-md bg-slate-800 px-2 py-1 text-xs font-semibold text-cyan-100">
                    {shipment.assigned_bunker || shipment.waste_code || "UNKNOWN"}
                  </span>
                </td>
                <td className="border-b border-slate-800 px-3 py-3">
                  <span className={`rounded-md px-2 py-1 text-xs font-semibold ${zoneTone(shipment.assigned_zone)}`}>
                    {shipment.assigned_zone || "MEDIUM"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
