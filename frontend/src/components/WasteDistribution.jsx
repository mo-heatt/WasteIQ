import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function DistributionTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="max-w-64 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 shadow-xl">
      <p className="text-sm font-semibold text-slate-100">{label}</p>
      <p className="text-sm text-cyan-100">{row.weight_tonnes} tonnes</p>
      <p className="text-xs text-slate-400">{row.waste_name}</p>
    </div>
  );
}

export default function WasteDistribution({ distribution = [] }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <div className="mb-4">
        <p className="text-sm font-medium text-slate-400">Waste-code distribution</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Tonnes by waste code</h2>
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={distribution} layout="vertical" margin={{ top: 8, right: 38, bottom: 8, left: 12 }}>
            <CartesianGrid stroke="#1f2b38" strokeDasharray="4 4" horizontal={false} />
            <XAxis type="number" stroke="#94a3b8" tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="waste_code" stroke="#cbd5e1" tickLine={false} axisLine={false} width={86} />
            <Tooltip content={<DistributionTooltip />} />
            <Bar dataKey="weight_tonnes" fill="#67e8f9" radius={[0, 4, 4, 0]} barSize={16}>
              <LabelList dataKey="weight_tonnes" position="right" fill="#cbd5e1" fontSize={12} formatter={(value) => `${value}t`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}
