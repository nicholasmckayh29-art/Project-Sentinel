"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = { date: string; output: number };

export function LineChartPanel({ data, title }: { data: Point[]; title: string }) {
  if (data.length === 0) {
    return (
      <div className="card-terminal p-4 h-64 flex items-center justify-center">
        <p className="font-mono text-xs text-muted">&gt; NO SNAPSHOT DATA</p>
      </div>
    );
  }

  return (
    <div className="card-terminal p-4 h-64">
      <h3 className="font-mono text-xs text-accent tracking-widest mb-2">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <CartesianGrid stroke="#2a2a2a" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 10 }} />
          <YAxis tick={{ fill: "#888", fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: "#111", border: "1px solid #2a2a2a", fontFamily: "monospace" }}
            labelStyle={{ color: "#00ff41" }}
          />
          <Line type="monotone" dataKey="output" stroke="#00ff41" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
