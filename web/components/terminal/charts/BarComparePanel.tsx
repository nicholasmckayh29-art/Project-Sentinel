"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type BarPoint = { name: string; output: number };

export function BarComparePanel({ data, title }: { data: BarPoint[]; title: string }) {
  if (data.length === 0) {
    return (
      <div className="card-terminal p-4 h-64 flex items-center justify-center">
        <p className="font-mono text-xs text-muted">&gt; SELECT MODELS TO COMPARE</p>
      </div>
    );
  }

  return (
    <div className="card-terminal p-4 h-64">
      <h3 className="font-mono text-xs text-accent tracking-widest mb-2">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data}>
          <CartesianGrid stroke="#2a2a2a" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fill: "#888", fontSize: 9 }} interval={0} angle={-20} textAnchor="end" height={50} />
          <YAxis tick={{ fill: "#888", fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: "#111", border: "1px solid #2a2a2a", fontFamily: "monospace" }}
          />
          <Bar dataKey="output" fill="#00ff41" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
