"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#00ff41", "#888888"];

export function PieCostPanel({
  inputPer1m,
  outputPer1m,
  title,
}: {
  inputPer1m: number;
  outputPer1m: number;
  title: string;
}) {
  const data = [
    { name: "Input $/1M", value: inputPer1m },
    { name: "Output $/1M", value: outputPer1m },
  ];
  const total = inputPer1m + outputPer1m;
  if (total <= 0) {
    return (
      <div className="card-terminal p-4 h-64 flex items-center justify-center">
        <p className="font-mono text-xs text-muted">&gt; NO PRICING DATA</p>
      </div>
    );
  }

  const inputPct = ((inputPer1m / total) * 100).toFixed(0);

  return (
    <div className="card-terminal p-4 h-64 flex flex-col">
      <h3 className="font-mono text-xs text-accent tracking-widest mb-2">{title}</h3>
      <div className="flex-1 min-h-[140px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="45%" innerRadius={36} outerRadius={58}>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Legend
              verticalAlign="bottom"
              iconType="circle"
              formatter={(value) => <span style={{ color: "#e0e0e0", fontFamily: "monospace", fontSize: 10 }}>{value}</span>}
            />
            <Tooltip
              contentStyle={{ background: "#111", border: "1px solid #2a2a2a", fontFamily: "monospace" }}
              itemStyle={{ color: "#e0e0e0" }}
              labelStyle={{ color: "#00ff41" }}
              formatter={(v: number) => [`$${v.toFixed(4)}`, ""]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <p className="font-mono text-[10px] text-muted text-center">
        IN ${inputPer1m.toFixed(4)} · OUT ${outputPer1m.toFixed(4)} · {inputPct}% input
      </p>
    </div>
  );
}
