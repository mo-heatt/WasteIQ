import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Database,
  Factory,
  GitCompare,
  Gauge,
  Layers3,
  Map,
  Package,
  Play,
  RefreshCcw,
  Route,
  ShieldCheck,
  SlidersHorizontal,
  Target,
  Timer,
  Truck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getChallenge1State,
  getBeforeAfterShipment,
  getDashboard,
  getDatasetSummary,
  getDefaultSimulation,
  getDemoSteps,
  getFuelArea,
  getImpact,
  getLayers,
  getOptimizerComparison,
  getRecommendation,
  getRegions,
  simulateMix,
} from "./api";

const NAV = [
  { id: "control", label: "Control Room", icon: Gauge },
  { id: "dataset", label: "Dataset", icon: Database },
  { id: "receiving", label: "Receiving Area", icon: Truck },
  { id: "challenge1", label: "Challenge 1 Input", icon: Factory },
  { id: "layers", label: "9-Layer Bunker Map", icon: Layers3 },
  { id: "regions", label: "Region Composition", icon: Map },
  { id: "beforeAfter", label: "Before / After Shipment", icon: RefreshCcw },
  { id: "funnel", label: "Funnel Optimizer", icon: GitCompare },
  { id: "fuel", label: "Fuel Area", icon: Package },
  { id: "agent", label: "Agent Mode", icon: Brain },
  { id: "demo", label: "Demo Mode", icon: Play },
  { id: "impact", label: "Impact", icon: BarChart3 },
];

const REGION_IDS = ["LEFT", "CENTER", "RIGHT"];
const REGION_STYLES = {
  LEFT: "text-sky-100 bg-sky-300/10 ring-sky-300/25",
  CENTER: "text-emerald-100 bg-emerald-300/10 ring-emerald-300/25",
  RIGHT: "text-amber-100 bg-amber-300/10 ring-amber-300/25",
};

function fmt(value, digits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return number.toFixed(digits);
}

function riskTone(status = "") {
  if (status.includes("CRITICAL")) return "bg-red-400/15 text-red-100 ring-red-300/30";
  if (status.includes("WARNING") || status.includes("HIGH")) return "bg-amber-300/15 text-amber-100 ring-amber-300/30";
  if (status.includes("SAFE") || status.includes("STABLE") || status === "AVAILABLE") return "bg-emerald-300/15 text-emerald-100 ring-emerald-300/30";
  return "bg-slate-400/15 text-slate-100 ring-slate-400/25";
}

function regionTone(region) {
  return REGION_STYLES[region] || "text-slate-100 bg-slate-300/10 ring-slate-300/25";
}

function PageTitle({ eyebrow, title, children }) {
  return (
    <div className="mb-5 flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/80">{eyebrow}</p>
      <h1 className="text-3xl font-bold text-white">{title}</h1>
      {children && <p className="max-w-4xl text-sm leading-6 text-slate-300">{children}</p>}
    </div>
  );
}

function StatCard({ label, value, icon: Icon = Activity, tone = "text-cyan-100" }) {
  return (
    <article className="control-panel rounded-lg p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
        <Icon className={`h-4 w-4 ${tone}`} />
      </div>
      <p className="mt-2 text-2xl font-bold text-white">{value ?? "—"}</p>
    </article>
  );
}

function ChallengeBadge({ state }) {
  const demo = state?.is_demo;
  return (
    <span className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ring-1 ${demo ? "bg-amber-300/15 text-amber-100 ring-amber-300/30" : "bg-emerald-300/15 text-emerald-100 ring-emerald-300/30"}`}>
      {demo ? "Demo Challenge 1 data" : "Using real Challenge 1 data"}
    </span>
  );
}

function DecisionLoop() {
  const steps = [
    ["Truck arrives", Truck],
    ["Waste code layer", Layers3],
    ["Unloading region", Map],
    ["9-layer map", Package],
    ["Funnel recipe", Target],
    ["Operator approves", CheckCircle2],
  ];
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">WasteIQ Decision Loop</p>
      <h2 className="mt-1 text-xl font-semibold text-white">From incoming truck to approved furnace feed</h2>
      <div className="mt-5 grid gap-3 md:grid-cols-6">
        {steps.map(([label, Icon], index) => (
          <div key={label} className="relative rounded-lg border border-slate-700/70 bg-slate-950/60 p-4">
            <Icon className="h-5 w-5 text-cyan-200" />
            <p className="mt-3 text-sm font-semibold text-white">{index + 1}. {label}</p>
            {index < steps.length - 1 && <ArrowRight className="absolute -right-4 top-1/2 hidden h-5 w-5 -translate-y-1/2 text-slate-500 md:block" />}
          </div>
        ))}
      </div>
    </article>
  );
}

function RegionCards({ regions = [] }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {regions.map((region) => (
        <article key={region.region_id} className={`control-panel rounded-lg p-5 ring-1 ${regionTone(region.region_id)}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase opacity-70">{region.region_id} region</p>
              <h3 className="mt-1 text-xl font-bold text-white">{region.operational_meaning}</h3>
            </div>
            <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${riskTone(region.region_status)}`}>{region.region_status}</span>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <StatCard label="Average CV" value={`${fmt(region.average_cv, 1)} MJ/kg`} icon={Gauge} />
            <StatCard label="Available mass" value={`${fmt(region.available_mass_tonnes, 1)} t`} icon={Factory} />
          </div>
          <div className="mt-4 h-2 rounded-full bg-slate-800">
            <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(Number(region.fill_percent || 0), 100)}%` }} />
          </div>
          <p className="mt-2 text-sm text-slate-400">Fill: {fmt(region.fill_percent, 0)}% · Dominant layer: {region.dominant_waste_code}</p>
        </article>
      ))}
    </div>
  );
}

function FunnelRecipe({ recommendation, title = "Recommended Funnel Feed — Next 2 Hours" }) {
  const optimized = recommendation?.optimized_region_mix || recommendation?.optimized_mix || recommendation;
  const simulation = recommendation?.simulation_result || optimized?.simulation || {};
  const mix = optimized?.recommended_region_mix || optimized?.mix_percentages || simulation.input_mix_percentages || {};
  const tonnes = simulation.crane_plan?.target_tonnes_by_region || simulation.consumed_by_region || {};
  const maxRisk = Math.round(Number(simulation.max_exhaustion_risk || 0) * 100);

  return (
    <article className="control-panel rounded-lg p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-cyan-100">What exactly should go into the furnace funnel next?</p>
          <h2 className="mt-1 text-2xl font-bold text-white">{title}</h2>
          <p className="mt-2 text-sm text-slate-400">Duration: next {fmt(simulation.duration_hours || 2, 0)} hours · Feed rate: {fmt(simulation.feed_rate_tonnes_per_hour || 10, 0)} t/hour · Total feed: {fmt(simulation.total_feed_mass_tonnes || 20, 1)} tonnes</p>
        </div>
        <span className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ring-1 ${simulation.is_cv_safe && simulation.is_feasible ? "bg-emerald-300/15 text-emerald-100 ring-emerald-300/30" : "bg-amber-300/15 text-amber-100 ring-amber-300/30"}`}>
          Operator approval required
        </span>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {REGION_IDS.map((region) => (
          <section key={region} className={`rounded-lg p-4 ring-1 ${regionTone(region)}`}>
            <p className="text-sm font-bold text-white">{region} region</p>
            <p className="mt-2 text-3xl font-black text-white">{fmt(mix[region] || 0, 0)}%</p>
            <p className="text-sm text-slate-300">= {fmt(tonnes[region] || 0, 1)} tonnes</p>
          </section>
        ))}
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <StatCard label="Expected blended CV" value={`${fmt(simulation.blended_cv || optimized?.expected_cv, 2)} MJ/kg`} icon={Gauge} />
        <StatCard label="Target CV" value="10 MJ/kg" icon={Target} />
        <StatCard label="Safe band" value="8–12 MJ/kg" icon={ShieldCheck} />
        <StatCard label="Region depletion risk" value={`${maxRisk}%`} icon={AlertTriangle} tone={maxRisk > 65 ? "text-amber-100" : "text-emerald-100"} />
      </div>
      <p className="mt-5 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-3 text-sm text-cyan-50">
        {optimized?.operator_instruction || simulation.crane_plan?.operator_instruction || "Review and approve this deterministic region recipe before feeding."}
      </p>
      <button className="mt-4 inline-flex items-center gap-2 rounded-md bg-emerald-300 px-4 py-3 text-sm font-bold text-slate-950">
        <CheckCircle2 className="h-4 w-4" />
        Approve feed plan
      </button>
    </article>
  );
}

function ForecastChart({ data = [] }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">2-hour forecast</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Predicted CV from optimized region recipe</h3>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" stroke="#94a3b8" />
            <YAxis domain={[7, 15]} stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
            <ReferenceLine y={8} stroke="#fb923c" strokeDasharray="5 5" label={{ value: "Lower safe limit", fill: "#fed7aa" }} />
            <ReferenceLine y={10} stroke="#67e8f9" strokeDasharray="5 5" label={{ value: "Target", fill: "#a5f3fc" }} />
            <ReferenceLine y={12} stroke="#f87171" strokeDasharray="5 5" label={{ value: "Upper safe limit", fill: "#fecaca" }} />
            <Line type="monotone" dataKey="cv" stroke="#22d3ee" strokeWidth={3} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function AgentCard({ explanation }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <div className="flex items-center gap-3">
        <Brain className="h-5 w-5 text-cyan-200" />
        <div>
          <p className="text-sm font-medium text-slate-400">AI explanation, deterministic calculation</p>
          <h3 className="text-xl font-semibold text-white">Operator reasoning</h3>
        </div>
      </div>
      {explanation?.thinking_sequence?.length > 0 && (
        <div className="mt-5 rounded-lg border border-slate-700/70 bg-slate-950/60 p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Agent thinking sequence</p>
          <div className="mt-3 space-y-2">
            {explanation.thinking_sequence.map((item) => (
              <p key={item} className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle2 className="h-4 w-4 text-cyan-200" />
                {item}
              </p>
            ))}
          </div>
        </div>
      )}
      <div className="mt-5 space-y-4 text-sm leading-6 text-slate-300">
        <p>{explanation?.summary}</p>
        <p>{explanation?.why_this_region_mix || explanation?.why_this_mix}</p>
        <p>{explanation?.how_9_layers_are_used}</p>
        <p>{explanation?.what_changed_after_latest_truck}</p>
        <p>{explanation?.zone_preservation_reasoning}</p>
        <p className="rounded-md border border-amber-300/20 bg-amber-300/10 p-3 text-amber-50">{explanation?.safety_note}</p>
      </div>
    </article>
  );
}

function TruckAssignmentCard({ assignment }) {
  if (!assignment) return null;
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">Latest incoming truck assignment</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Where should this truck unload?</h3>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <StatCard label="Truck ID" value={assignment.truck_id} icon={Truck} />
        <StatCard label="Waste-code layer" value={assignment.waste_code} icon={Layers3} />
        <StatCard label="CV" value={`${fmt(assignment.cv, 1)} MJ/kg`} icon={Gauge} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className={`rounded-lg p-4 ring-1 ${regionTone(assignment.recommended_unloading_region)}`}>
          <p className="text-xs uppercase opacity-70">Recommended unloading region</p>
          <p className="mt-2 text-3xl font-black text-white">{assignment.recommended_unloading_region}</p>
          <p className="mt-1 text-sm text-slate-300">{assignment.recommended_region_meaning}</p>
        </div>
        <div className="rounded-lg border border-slate-700/70 bg-slate-950/60 p-4">
          <p className="text-xs uppercase text-slate-500">Operator instruction</p>
          <p className="mt-2 text-lg font-semibold text-white">{assignment.operator_instruction}</p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">{assignment.reason}</p>
      <p className="mt-3 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-3 text-sm text-cyan-50">
        The bunker remains one open pit. WasteIQ guides unloading into approximate operational regions and tracks the expected 9-layer CV distribution virtually.
      </p>
    </article>
  );
}

function ControlRoom({ dashboard, recommendation }) {
  return (
    <section>
      <PageTitle eyebrow="Control Room" title="WasteIQ Control Center">
        WasteIQ does not require physical reconstruction of the bunker. It uses shipment records and Challenge 1 bunker availability to create a software-defined 9-layer energy map.
      </PageTitle>
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Current bunker CV" value={`${fmt(dashboard.current_cv, 2)} MJ/kg`} icon={Gauge} tone={dashboard.risk_status?.includes("WARNING") ? "text-amber-100" : "text-emerald-100"} />
        <StatCard label="Target CV" value="10 MJ/kg" icon={Target} />
        <StatCard label="Safe operating band" value="8–12 MJ/kg" icon={ShieldCheck} />
        <article className="control-panel rounded-lg p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Challenge 1 status</p>
          <div className="mt-3"><ChallengeBadge state={dashboard.challenge1_state} /></div>
        </article>
      </div>
      <div className="mt-5"><DecisionLoop /></div>
      <div className="mt-5"><TruckAssignmentCard assignment={dashboard.latest_truck_assignment} /></div>
      <div className="mt-5"><RegionCards regions={dashboard.regions} /></div>
      <div className="mt-5"><FunnelRecipe recommendation={recommendation} /></div>
      <div className="mt-5"><OperatorSteps steps={recommendation?.operator_steps || dashboard.operator_steps} /></div>
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <ForecastChart data={recommendation?.forecast || dashboard.forecast} />
        <AgentCard explanation={recommendation?.agent_explanation} />
      </div>
    </section>
  );
}

function DatasetPage({ dataset }) {
  return (
    <section>
      <PageTitle eyebrow="Dataset Explorer" title="Shipment records transform truck deliveries into energy-aware bunker data." />
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Total shipments" value={dataset.total_shipments} icon={Database} />
        <StatCard label="Total tonnes" value={`${fmt(dataset.total_weight_tonnes, 1)} t`} icon={Factory} />
        <StatCard label="Unique waste codes" value={dataset.unique_waste_codes?.length || 0} icon={Route} />
        <StatCard label="First timestamp" value={dataset.first_timestamp ? new Date(dataset.first_timestamp).toLocaleTimeString() : "—"} icon={Timer} />
        <StatCard label="Latest timestamp" value={dataset.latest_timestamp ? new Date(dataset.latest_timestamp).toLocaleTimeString() : "—"} icon={Timer} />
        <StatCard label="Missing fields" value={(dataset.missing_weight_count || 0) + (dataset.missing_waste_code_count || 0)} icon={AlertTriangle} />
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <article className="control-panel rounded-lg p-5">
          <p className="text-sm font-medium text-slate-400">Waste-code distribution</p>
          <div className="mt-4 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dataset.waste_code_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="waste_code" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }} />
                <Bar dataKey="weight_tonnes" fill="#22d3ee" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
        <ShipmentTable shipments={dataset.latest_shipments} />
      </div>
    </section>
  );
}

function ReceivingAreaPage({ dashboard }) {
  const assignments = dashboard.recent_truck_assignments || [];
  return (
    <section>
      <PageTitle eyebrow="Receiving Area" title="Truck Intake → Recommended unloading region">
        Each arriving truck is mapped to a waste-code layer, checked against Challenge 1 capacity, and assigned to LEFT, CENTER or RIGHT.
      </PageTitle>
      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <TruckAssignmentCard assignment={dashboard.latest_truck_assignment} />
        <article className="control-panel rounded-lg p-5">
          <p className="text-sm font-medium text-slate-400">Operational flow</p>
          <h3 className="mt-1 text-xl font-semibold text-white">Truck Intake → Receiving Area → Guided unloading region</h3>
          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            {["Truck Intake", "Waste-code layer", "Capacity check", "Moved"].map((label, index) => (
              <div key={label} className="rounded-lg border border-slate-700/70 bg-slate-950/60 p-4">
                <p className="text-xs uppercase text-slate-500">Step {index + 1}</p>
                <p className="mt-2 font-bold text-white">{label}</p>
              </div>
            ))}
          </div>
          <p className="mt-5 rounded-md border border-cyan-300/20 bg-cyan-300/10 p-3 text-sm text-cyan-50">
            Status values are demo operational states: waiting, assigned and moved. WasteIQ recommends; the plant operator executes.
          </p>
        </article>
      </div>
      <article className="control-panel mt-5 overflow-hidden rounded-lg">
        <div className="border-b border-slate-700/80 p-5">
          <p className="text-sm font-medium text-slate-400">Recent receiving assignments</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>{["Time", "Truck", "Waste code", "Mass", "CV", "Region", "Fallback", "Status"].map((head) => <th key={head} className="border-b border-slate-700/80 px-4 py-3">{head}</th>)}</tr>
            </thead>
            <tbody>
              {assignments.map((item, index) => (
                <tr key={`${item.truck_id}-${item.timestamp}-${index}`} className="border-b border-slate-800/80 text-slate-300">
                  <td className="px-4 py-3">{item.timestamp ? new Date(item.timestamp).toLocaleString() : "—"}</td>
                  <td className="px-4 py-3 text-white">{item.truck_id}</td>
                  <td className="px-4 py-3">{item.waste_code}</td>
                  <td className="px-4 py-3">{fmt(item.weight_tonnes, 1)} t</td>
                  <td className="px-4 py-3">{fmt(item.cv, 1)}</td>
                  <td className="px-4 py-3"><span className={`rounded-md px-2 py-1 text-xs font-bold ring-1 ${regionTone(item.recommended_unloading_region)}`}>{item.recommended_unloading_region}</span></td>
                  <td className="px-4 py-3">{item.fallback_used ? "YES" : "NO"}</td>
                  <td className="px-4 py-3">{index === 0 ? "assigned" : "moved"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function ShipmentTable({ shipments = [] }) {
  return (
    <article className="control-panel overflow-hidden rounded-lg">
      <div className="border-b border-slate-700/80 p-5">
        <p className="text-sm font-medium text-slate-400">Latest shipments</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[780px] text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              {["Time", "Truck", "Waste code", "Waste name", "Weight", "CV", "Layer"].map((head) => (
                <th key={head} className="border-b border-slate-700/80 px-4 py-3 font-semibold">{head}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shipments.map((shipment, index) => (
              <tr key={`${shipment.truck_id}-${shipment.timestamp}-${index}`} className="border-b border-slate-800/80 text-slate-300">
                <td className="px-4 py-3">{shipment.timestamp ? new Date(shipment.timestamp).toLocaleString() : "—"}</td>
                <td className="px-4 py-3 text-white">{shipment.truck_id}</td>
                <td className="px-4 py-3">{shipment.waste_code}</td>
                <td className="px-4 py-3">{shipment.waste_name}</td>
                <td className="px-4 py-3">{fmt(shipment.weight_tonnes, 1)} t</td>
                <td className="px-4 py-3">{fmt(shipment.cv, 1)}</td>
                <td className="px-4 py-3">{shipment.waste_layer_id || shipment.waste_code}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function Challenge1Page({ challenge1 }) {
  return (
    <section>
      <PageTitle eyebrow="Challenge 1 Input" title="Bunker region capacity from images.">
        Challenge 1 estimates bunker region capacity from images. WasteIQ uses that capacity to optimize furnace feeding.
      </PageTitle>
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Source" value={challenge1.status_label || challenge1.source} icon={Factory} />
        <StatCard label="Total fill" value={`${fmt(challenge1.total_fill_percent, 0)}%`} icon={Gauge} />
        <StatCard label="Timestamp" value={challenge1.timestamp || "—"} icon={Timer} />
        <article className="control-panel rounded-lg p-4"><ChallengeBadge state={challenge1} /></article>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {(challenge1.regions || []).map((region) => (
          <article key={region.region_id} className={`control-panel rounded-lg p-5 ring-1 ${regionTone(region.region_id)}`}>
            <h3 className="text-2xl font-bold text-white">{region.region_id}</h3>
            <p className="mt-3 text-4xl font-black text-white">{fmt(region.available_mass_tonnes, 1)} t</p>
            <p className="text-sm text-slate-400">available mass</p>
            <div className="mt-5 h-2 rounded-full bg-slate-800">
              <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(Number(region.fill_percent || 0), 100)}%` }} />
            </div>
            <p className="mt-2 text-sm text-slate-300">{fmt(region.fill_percent, 0)}% full</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function LayerMapPage({ layers }) {
  return (
    <section>
      <PageTitle eyebrow="9-Layer Bunker Map" title="virtual waste-code layers, not walls or separate storage areas.">
        WasteIQ tracks the 9 waste-code layers internally, then turns them into a LEFT/CENTER/RIGHT region recipe for the operator.
      </PageTitle>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(layers.layers || []).map((layer) => {
          const heat = Math.min(1, Math.max(0, (Number(layer.cv) - 9) / 9));
          return (
            <article key={layer.waste_code} className="control-panel rounded-lg p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase text-slate-500">{layer.waste_code}</p>
                  <h3 className="mt-1 text-lg font-bold text-white">{layer.name}</h3>
                </div>
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${regionTone(layer.preferred_region)}`}>{layer.preferred_region}</span>
              </div>
              <div className="mt-5 h-2 rounded-full bg-slate-800">
                <div className="h-2 rounded-full" style={{ width: `${Math.min(Number(layer.percentage_of_bunker || 0), 100)}%`, backgroundColor: `rgb(${80 + heat * 180}, ${220 - heat * 130}, 140)` }} />
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <StatCard label="CV" value={fmt(layer.cv, 1)} />
                <StatCard label="Mass" value={`${fmt(layer.total_estimated_mass_tonnes, 1)} t`} />
                <StatCard label="Share" value={`${fmt(layer.percentage_of_bunker, 1)}%`} />
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function RegionCompositionPage({ regions }) {
  return (
    <section>
      <PageTitle eyebrow="Region Composition" title="LEFT/CENTER/RIGHT average CV from 9-layer composition.">
        Each region’s average CV is calculated from its estimated waste-code layer composition.
      </PageTitle>
      <RegionCards regions={regions.regions || []} />
      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        {(regions.regions || []).map((region) => (
          <article key={region.region_id} className="control-panel rounded-lg p-5">
            <h3 className="text-xl font-bold text-white">{region.region_id} composition</h3>
            <p className="mt-1 text-sm text-slate-400">Dominant layer: {region.dominant_waste_code}</p>
            <div className="mt-5 space-y-3">
              {(region.waste_layer_composition || []).filter((layer) => Number(layer.estimated_mass_tonnes) > 0).map((layer) => (
                <div key={layer.waste_code}>
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-white">{layer.waste_code}</span>
                    <span className="text-slate-300">{fmt(layer.estimated_mass_tonnes, 1)} t · {fmt(layer.percentage_of_region, 0)}%</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-slate-800">
                    <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(Number(layer.percentage_of_region || 0), 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function FunnelSimulatorPage({ defaultSimulation }) {
  const [left, setLeft] = useState(33);
  const [center, setCenter] = useState(34);
  const [right, setRight] = useState(33);
  const [feedRate, setFeedRate] = useState(10);
  const [duration, setDuration] = useState(2);
  const [result, setResult] = useState(defaultSimulation);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const sum = left + center + right;

  async function runSimulation() {
    setError("");
    if (sum !== 100) {
      setError("LEFT, CENTER and RIGHT percentages must sum to 100.");
      return;
    }
    setLoading(true);
    try {
      const response = await simulateMix({ left_pct: left, center_pct: center, right_pct: right, feed_rate_tonnes_per_hour: feedRate, duration_hours: duration });
      setResult(response.simulation);
    } catch (err) {
      setError(err.message || "Simulation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <PageTitle eyebrow="Funnel Simulator" title="Test any LEFT/CENTER/RIGHT funnel feed recipe." />
      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <article className="control-panel rounded-lg p-5">
          <p className="text-sm font-medium text-slate-400">2-hour region depletion simulation</p>
          <div className="mt-5 grid gap-4">
            {[["LEFT %", left, setLeft], ["CENTER %", center, setCenter], ["RIGHT %", right, setRight]].map(([label, value, setter]) => (
              <label key={label}>
                <span className="flex justify-between text-xs font-semibold uppercase text-slate-500"><span>{label}</span><span>{value}%</span></span>
                <input type="range" min="0" max="100" step="5" value={value} onChange={(event) => setter(Number(event.target.value))} className="mt-2 w-full accent-cyan-300" />
              </label>
            ))}
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <label><span className="text-xs uppercase text-slate-500">Feed rate t/hour</span><input className="mt-2 h-11 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-white" type="number" min="1" value={feedRate} onChange={(event) => setFeedRate(Number(event.target.value))} /></label>
            <label><span className="text-xs uppercase text-slate-500">Duration hours</span><input className="mt-2 h-11 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-white" type="number" min="0.5" step="0.5" value={duration} onChange={(event) => setDuration(Number(event.target.value))} /></label>
          </div>
          <div className="mt-5 flex items-center justify-between gap-3">
            <p className={sum === 100 ? "text-emerald-100" : "text-amber-100"}>Current sum: {sum}%</p>
            <button onClick={runSimulation} disabled={loading} className="inline-flex h-11 items-center gap-2 rounded-md bg-cyan-300 px-4 text-sm font-bold text-slate-950">
              <Play className="h-4 w-4" /> {loading ? "Simulating" : "Simulate Mix"}
            </button>
          </div>
          {error && <p className="mt-4 rounded-md border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">{error}</p>}
        </article>
        <article className="control-panel rounded-lg p-5">
          <h3 className="text-xl font-semibold text-white">Simulation result</h3>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <StatCard label="Blended CV" value={`${fmt(result?.blended_cv, 2)} MJ/kg`} icon={Gauge} />
            <StatCard label="Target error" value={fmt(result?.target_error, 2)} icon={Target} />
            <StatCard label="Safe / unsafe" value={result?.is_cv_safe ? "SAFE" : "REVIEW"} icon={ShieldCheck} tone={result?.is_cv_safe ? "text-emerald-100" : "text-amber-100"} />
          </div>
          <RegionDepletion simulation={result} />
        </article>
      </div>
    </section>
  );
}

function RegionDepletion({ simulation = {} }) {
  return (
    <div className="mt-5 grid gap-3 md:grid-cols-3">
      {REGION_IDS.map((region) => {
        const risk = Number(simulation.exhaustion_risk_by_region?.[region] || 0);
        return (
          <article key={region} className={`rounded-lg p-4 ring-1 ${regionTone(region)}`}>
            <p className="font-bold text-white">{region}</p>
            <p className="mt-2 text-sm text-slate-300">Consumed: {fmt(simulation.consumed_by_region?.[region], 1)} t</p>
            <p className="text-sm text-slate-300">Remaining: {fmt(simulation.remaining_by_region?.[region], 1)} t</p>
            <div className="mt-3 h-2 rounded-full bg-slate-800">
              <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(risk * 100, 100)}%` }} />
            </div>
            <p className="mt-1 text-xs text-slate-400">{Math.round(risk * 100)}% depletion risk</p>
          </article>
        );
      })}
    </div>
  );
}

function RegionSnapshot({ title, state }) {
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">{title}</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Bunker state</h3>
      <div className="mt-5 space-y-3">
        {(state?.regions || []).map((region) => (
          <div key={region.region_id} className={`rounded-lg p-4 ring-1 ${regionTone(region.region_id)}`}>
            <div className="flex justify-between gap-3">
              <p className="font-bold text-white">{region.region_id}</p>
              <p className="text-sm text-slate-300">{fmt(region.available_mass_tonnes, 1)}t · avg CV {fmt(region.average_cv, 1)}</p>
            </div>
            <p className="mt-1 text-xs text-slate-400">Dominant layer: {region.dominant_waste_code} · fill {fmt(region.fill_percent, 0)}%</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function RecipeMini({ title, recipe }) {
  const simulation = recipe?.simulation || {};
  const mix = recipe?.recommended_region_mix || recipe?.mix_percentages || {};
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">{title}</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Expected CV {fmt(simulation.blended_cv || recipe?.expected_cv, 2)} MJ/kg</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {REGION_IDS.map((region) => (
          <div key={region} className={`rounded-lg p-3 ring-1 ${regionTone(region)}`}>
            <p className="text-xs uppercase opacity-70">{region}</p>
            <p className="mt-1 text-2xl font-black text-white">{fmt(mix[region] || 0, 0)}%</p>
            <p className="text-xs text-slate-300">{fmt(simulation.consumed_by_region?.[region], 1)} t</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-slate-300">{recipe?.operator_instruction}</p>
    </article>
  );
}

function BeforeAfterPage({ beforeAfter }) {
  const shipment = beforeAfter?.next_shipment;
  return (
    <section>
      <PageTitle eyebrow="Before / After Next Shipment" title="Dynamic update after the latest truck">
        This proves WasteIQ recalculates the virtual 9-layer map, region CVs and 2-hour funnel recipe as new trucks arrive.
      </PageTitle>
      <div className="grid gap-5 xl:grid-cols-2">
        <RegionSnapshot title="Before next shipment" state={beforeAfter?.before?.virtual_bunker_map} />
        <div className="space-y-5">
          <article className="control-panel rounded-lg p-5">
            <p className="text-sm font-medium text-slate-400">Latest or simulated next truck</p>
            <h3 className="mt-1 text-xl font-semibold text-white">{shipment?.truck_id || "No truck"}</h3>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <StatCard label="Waste code" value={shipment?.waste_code} icon={Layers3} />
              <StatCard label="Mass" value={`${fmt(shipment?.weight_tonnes, 1)} t`} icon={Truck} />
              <StatCard label="CV" value={`${fmt(shipment?.cv, 1)} MJ/kg`} icon={Gauge} />
            </div>
          </article>
          <TruckAssignmentCard assignment={beforeAfter?.assignment} />
        </div>
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <RegionSnapshot title="After unloading" state={beforeAfter?.after?.virtual_bunker_map} />
        <div>
          <article className="control-panel rounded-lg p-5">
            <p className="text-sm font-medium text-slate-400">How the 2-hour feed plan changed</p>
            <h3 className="mt-1 text-xl font-semibold text-white">{beforeAfter?.feed_plan_change}</h3>
          </article>
          <div className="mt-5 grid gap-5 xl:grid-cols-2">
            <RecipeMini title="Old funnel recipe" recipe={beforeAfter?.old_funnel_recipe} />
            <RecipeMini title="New funnel recipe" recipe={beforeAfter?.new_funnel_recipe} />
          </div>
        </div>
      </div>
    </section>
  );
}

function OptimizerCard({ title, data }) {
  const simulation = data?.simulation || {};
  return (
    <article className="control-panel rounded-lg p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xl font-bold text-white">{title}</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${simulation.is_cv_safe && simulation.is_feasible ? "bg-emerald-300/15 text-emerald-100 ring-emerald-300/30" : "bg-amber-300/15 text-amber-100 ring-amber-300/30"}`}>{simulation.is_cv_safe ? "SAFE" : "REVIEW"}</span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {REGION_IDS.map((region) => <StatCard key={region} label={`${region} %`} value={`${fmt(data?.mix_percentages?.[region] || 0, 0)}%`} />)}
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <StatCard label="Blended CV" value={`${fmt(simulation.blended_cv, 2)} MJ/kg`} icon={Gauge} />
        <StatCard label="Target error" value={fmt(simulation.target_error, 2)} icon={Target} />
        <StatCard label="Max exhaustion" value={`${Math.round(Number(simulation.max_exhaustion_risk || 0) * 100)}%`} icon={AlertTriangle} />
      </div>
      <RegionDepletion simulation={simulation} />
    </article>
  );
}

function OptimizerPage({ optimizer }) {
  return (
    <section>
      <PageTitle eyebrow="Optimizer" title="Naive Equal Region Mix vs Optimized Region Mix">
        The optimized mix keeps CV near target while preserving bunker flexibility.
      </PageTitle>
      <div className="grid gap-5 xl:grid-cols-2">
        <OptimizerCard title="Naive Equal Region Mix" data={optimizer.naive_region_mix_result || optimizer.naive_mix} />
        <OptimizerCard title="Optimized Region Mix" data={optimizer.optimized_region_mix_result || optimizer.optimized_mix} />
      </div>
      <article className="control-panel mt-5 rounded-lg p-5">
        <h3 className="text-xl font-semibold text-white">Improvement summary</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <StatCard label="Target error reduction" value={optimizer.improvement_summary?.target_error_reduction} icon={Target} />
          <StatCard label="Region preservation improvement" value={`${optimizer.improvement_summary?.region_preservation_improvement_percent ?? 0}%`} icon={ShieldCheck} />
          <StatCard label="Score reduction" value={optimizer.improvement_summary?.score_reduction} icon={GitCompare} />
        </div>
        <p className="mt-4 text-slate-300">{optimizer.why_optimized_is_better}</p>
      </article>
    </section>
  );
}

function FunnelOptimizerPage({ defaultSimulation, optimizer }) {
  return (
    <div className="space-y-8">
      <FunnelSimulatorPage defaultSimulation={defaultSimulation} />
      <OptimizerPage optimizer={optimizer} />
    </div>
  );
}

function OperatorSteps({ steps = [] }) {
  if (!steps?.length) return null;
  return (
    <article className="control-panel rounded-lg p-5">
      <p className="text-sm font-medium text-slate-400">Next 5 Operator Steps</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Generated from the optimized recommendation</h3>
      <div className="mt-5 grid gap-3 md:grid-cols-5">
        {steps.map((step) => (
          <div key={step.step} className="rounded-lg border border-slate-700/70 bg-slate-950/60 p-4">
            <p className="text-xs font-semibold uppercase text-cyan-200">Step {step.step}</p>
            <p className="mt-2 text-sm font-semibold text-white">{step.instruction}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {(step.keywords || []).map((keyword) => (
                <span key={keyword} className="rounded bg-cyan-300/10 px-2 py-1 text-[10px] font-bold text-cyan-100">{keyword}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function FuelAreaPage({ fuelArea }) {
  const blend = fuelArea?.fuel_blend || {};
  return (
    <section>
      <PageTitle eyebrow="Fuel Area" title="Final blended fuel mix ready for furnace review">
        The Fuel Area reflects the optimized LEFT/CENTER/RIGHT recipe and preserves full waste-code composition.
      </PageTitle>
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Average CV" value={`${fmt(blend.average_cv, 2)} MJ/kg`} icon={Gauge} />
        <StatCard label="Total fuel mass" value={`${fmt(blend.total_mass_tonnes, 1)} t`} icon={Package} />
        <StatCard label="Safe / unsafe" value={blend.is_safe ? "SAFE" : "REVIEW"} icon={ShieldCheck} tone={blend.is_safe ? "text-emerald-100" : "text-amber-100"} />
        <StatCard label="Furnace status" value={blend.furnace_ready_status} icon={Factory} />
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <article className="control-panel rounded-lg p-5">
          <p className="text-sm font-medium text-slate-400">Mass pulled from regions</p>
          <div className="mt-5 space-y-3">
            {REGION_IDS.map((region) => (
              <div key={region} className={`rounded-lg p-4 ring-1 ${regionTone(region)}`}>
                <div className="flex justify-between">
                  <p className="font-bold text-white">{region}</p>
                  <p className="text-slate-300">{fmt(blend.pulled_mass_by_region?.[region], 1)} t</p>
                </div>
              </div>
            ))}
          </div>
        </article>
        <article className="control-panel rounded-lg p-5">
          <p className="text-sm font-medium text-slate-400">Waste-code composition inside fuel mix</p>
          <div className="mt-5 space-y-3">
            {(blend.waste_code_composition || []).map((layer) => (
              <div key={layer.waste_code}>
                <div className="flex justify-between gap-3 text-sm">
                  <span className="font-semibold text-white">{layer.waste_code} · {layer.name}</span>
                  <span className="text-slate-300">{fmt(layer.estimated_mass_tonnes, 1)} t · {fmt(layer.percentage_of_fuel_mix, 0)}%</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(Number(layer.percentage_of_fuel_mix || 0), 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </article>
      </div>
      <div className="mt-5"><OperatorSteps steps={fuelArea?.operator_steps} /></div>
    </section>
  );
}

function AgentModePage({ recommendation }) {
  return (
    <section>
      <PageTitle eyebrow="Agent Mode" title="AI explanation, deterministic calculation">
        The agent does not calculate. It explains the deterministic 9-layer map, region simulation and optimized furnace feed recommendation.
      </PageTitle>
      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <AgentCard explanation={recommendation?.agent_explanation} />
        <FunnelRecipe recommendation={recommendation} title="Agent-presented funnel recipe" />
      </div>
    </section>
  );
}

function DemoPage({ steps }) {
  const [stepIndex, setStepIndex] = useState(0);
  const step = steps[stepIndex] || steps[0];
  return (
    <section>
      <PageTitle eyebrow="Demo Mode" title="Guided Judge Demo">
        Bunker is one open pit → 9 waste-code layers → region CVs → optimized LEFT/CENTER/RIGHT funnel recipe.
      </PageTitle>
      <div className="grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
        <article className="control-panel rounded-lg p-5">
          <button onClick={() => setStepIndex(0)} className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950"><Play className="h-4 w-4" />Start Judge Demo</button>
          <div className="mt-5 space-y-2">
            {steps.map((item, index) => (
              <button key={item.step} onClick={() => setStepIndex(index)} className={`flex w-full gap-3 rounded-md px-3 py-2 text-left text-sm ${index === stepIndex ? "bg-cyan-300 text-slate-950" : "bg-slate-900 text-slate-300"}`}>
                <span className="font-bold">{item.step}</span><span>{item.title}</span>
              </button>
            ))}
          </div>
        </article>
        <article className="control-panel rounded-lg p-8">
          <p className="text-sm text-slate-400">Step {step?.step} of {steps.length}</p>
          <h2 className="mt-2 text-3xl font-bold text-white">{step?.title}</h2>
          <p className="mt-4 text-lg leading-8 text-slate-300">{step?.description}</p>
          <div className="mt-8 flex gap-3">
            <button onClick={() => setStepIndex(Math.max(0, stepIndex - 1))} className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-200"><ChevronLeft className="h-4 w-4" />Back</button>
            <button onClick={() => setStepIndex(Math.min(steps.length - 1, stepIndex + 1))} className="inline-flex items-center gap-2 rounded-md bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950">Next<ChevronRight className="h-4 w-4" /></button>
          </div>
        </article>
      </div>
    </section>
  );
}

function ImpactPage({ impact }) {
  return (
    <section>
      <PageTitle eyebrow="Impact Summary" title="Operational value for judges." />
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Target CV" value={`${impact.target_cv || impact.cv_target} MJ/kg`} icon={Target} />
        <StatCard label="Safe band" value={impact.safe_band || impact.safe_range} icon={ShieldCheck} />
        <StatCard label="Operator decision time" value={impact.operator_decision_time} icon={Timer} />
        <StatCard label="Naive target error" value={impact.naive_target_error} icon={AlertTriangle} />
        <StatCard label="Optimized target error" value={impact.optimized_target_error} icon={CheckCircle2} />
        <StatCard label="Region preservation improvement" value={`${impact.region_preservation_improvement_percent ?? impact.zone_preservation_improvement_percent}%`} icon={Map} />
      </div>
      <article className="control-panel mt-5 rounded-lg p-8">
        <h3 className="max-w-4xl text-3xl font-bold text-white">{impact.summary}</h3>
        <p className="mt-5 text-lg text-cyan-100">WasteIQ converts one open bunker into a software-defined 9-layer energy map and recommends the safest balanced region-based feed mix for the furnace funnel.</p>
      </article>
    </section>
  );
}

function Layout({ activePage, setActivePage, children, status }) {
  return (
    <main className="min-h-screen bg-[#081017] text-slate-100 subtle-grid">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 border-r border-slate-800/80 bg-slate-950/80 p-5 lg:block">
          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-200">WasteIQ</p>
            <h1 className="mt-2 text-2xl font-black text-white">Control Center</h1>
            <span className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${riskTone(status)}`}>{status}</span>
          </div>
          <nav className="space-y-2">
            {NAV.map((item) => {
              const Icon = item.icon;
              return (
                <button key={item.id} onClick={() => setActivePage(item.id)} className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition ${activePage === item.id ? "bg-cyan-300 text-slate-950" : "text-slate-300 hover:bg-slate-900"}`}>
                  <Icon className="h-4 w-4" /> {item.label}
                </button>
              );
            })}
          </nav>
        </aside>
        <section className="min-w-0 flex-1 p-4 lg:p-8">
          <div className="mb-5 flex gap-2 overflow-x-auto lg:hidden">
            {NAV.map((item) => <button key={item.id} onClick={() => setActivePage(item.id)} className={`shrink-0 rounded-md px-3 py-2 text-sm ${activePage === item.id ? "bg-cyan-300 text-slate-950" : "bg-slate-900 text-slate-200"}`}>{item.label}</button>)}
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}

function LoadingState() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#081017] text-slate-100 subtle-grid">
      <section className="control-panel rounded-lg p-8 text-center">
        <Activity className="mx-auto h-10 w-10 animate-pulse text-cyan-300" />
        <p className="mt-4 text-xl font-semibold">Loading WasteIQ Control Center</p>
        <p className="mt-2 text-sm text-slate-400">Preparing 9-layer map, regions, simulator and optimizer.</p>
      </section>
    </main>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#081017] text-slate-100 subtle-grid">
      <section className="control-panel max-w-xl rounded-lg p-8">
        <div className="flex gap-3">
          <AlertTriangle className="h-6 w-6 text-amber-200" />
          <div><h1 className="text-xl font-bold text-white">Backend unavailable</h1><p className="mt-2 text-sm text-slate-300">{message}</p></div>
        </div>
        <button onClick={onRetry} className="mt-6 inline-flex items-center gap-2 rounded-md bg-cyan-300 px-4 py-2 text-sm font-bold text-slate-950"><RefreshCcw className="h-4 w-4" />Retry</button>
      </section>
    </main>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("control");
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [dashboard, dataset, challenge1, layers, regions, defaultSimulation, optimizer, recommendation, beforeAfter, fuelArea, demoSteps, impact] = await Promise.all([
        getDashboard(),
        getDatasetSummary(),
        getChallenge1State(),
        getLayers(),
        getRegions(),
        getDefaultSimulation(),
        getOptimizerComparison(),
        getRecommendation(),
        getBeforeAfterShipment(),
        getFuelArea(),
        getDemoSteps(),
        getImpact(),
      ]);
      setState({ dashboard, dataset, challenge1, layers, regions, defaultSimulation: defaultSimulation.simulation, optimizer, recommendation, beforeAfter, fuelArea, demoSteps, impact });
    } catch (err) {
      setError(err.message || "WasteIQ could not reach the backend service.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  const pages = useMemo(() => {
    if (!state) return {};
    return {
      control: <ControlRoom dashboard={state.dashboard} recommendation={state.recommendation} />,
      dataset: <DatasetPage dataset={state.dataset} />,
      receiving: <ReceivingAreaPage dashboard={state.dashboard} />,
      challenge1: <Challenge1Page challenge1={state.challenge1} />,
      layers: <LayerMapPage layers={state.layers} />,
      regions: <RegionCompositionPage regions={state.regions} />,
      beforeAfter: <BeforeAfterPage beforeAfter={state.beforeAfter} />,
      funnel: <FunnelOptimizerPage defaultSimulation={state.defaultSimulation} optimizer={state.optimizer} />,
      fuel: <FuelAreaPage fuelArea={state.fuelArea} />,
      agent: <AgentModePage recommendation={state.recommendation} />,
      demo: <DemoPage steps={state.demoSteps} />,
      impact: <ImpactPage impact={state.impact} />,
    };
  }, [state]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={loadAll} />;

  return (
    <Layout activePage={activePage} setActivePage={setActivePage} status={state.dashboard.risk_status}>
      {pages[activePage] || pages.control}
    </Layout>
  );
}
