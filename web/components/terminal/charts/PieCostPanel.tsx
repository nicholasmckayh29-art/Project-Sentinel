"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

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

  return (
    <div className="card-terminal p-4 h-64">
      <h3 className="font-mono text-xs text-accent tracking-widest mb-2">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#111", border: "1px solid #2a2a2a", fontFamily: "monospace" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
