import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 shadow-xl">
      <p className="text-sm font-semibold text-slate-100">{label}</p>
      <p className="text-sm text-cyan-100">{payload[0].value} MJ/kg</p>
    </div>
  );
}

export default function CVForecastChart({ forecast = [] }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <div className="mb-4">
        <p className="text-sm font-medium text-slate-400">Predicted CV drift</p>
        <h2 className="mt-1 text-xl font-semibold text-white">2-hour optimized feed forecast</h2>
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={forecast} margin={{ top: 18, right: 20, bottom: 10, left: 0 }}>
            <CartesianGrid stroke="#1f2b38" strokeDasharray="4 4" />
            <XAxis dataKey="label" stroke="#94a3b8" tickLine={false} axisLine={false} />
            <YAxis domain={[6, 16]} stroke="#94a3b8" tickLine={false} axisLine={false} width={42} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceArea y1={9.8} y2={10.2} fill="#22c55e" fillOpacity={0.08} />
            <ReferenceLine y={8} stroke="#f97316" strokeDasharray="6 6" label={{ value: "Lower safe limit", fill: "#fed7aa", position: "insideRight" }} />
            <ReferenceLine y={10} stroke="#67e8f9" strokeDasharray="6 6" label={{ value: "Target", fill: "#a5f3fc", position: "insideRight" }} />
            <ReferenceLine y={12} stroke="#f97316" strokeDasharray="6 6" label={{ value: "Upper safe limit", fill: "#fed7aa", position: "insideRight" }} />
            <Line
              type="monotone"
              dataKey="cv"
              stroke="#67e8f9"
              strokeWidth={3}
              dot={{ r: 5, strokeWidth: 2, fill: "#081017", stroke: "#67e8f9" }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}
