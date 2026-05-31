"use client";

import { ProviderLogo } from "@/components/terminal/ProviderLogo";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

type WatchlistModel = {
  model_id: string;
  display_name: string;
  provider_id: string;
};

export function ModelPicker({
  models,
  selected,
  maxSelect = 3,
}: {
  models: WatchlistModel[];
  selected: string[];
  maxSelect?: number;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const toggle = useCallback(
    (modelId: string) => {
      let next: string[];
      if (selected.includes(modelId)) {
        next = selected.filter((id) => id !== modelId);
      } else if (selected.length >= maxSelect) {
        next = [...selected.slice(1), modelId];
      } else {
        next = [...selected, modelId];
      }
      const params = new URLSearchParams(searchParams.toString());
      if (next.length) params.set("models", next.join(","));
      else params.delete("models");
      router.push(`/desk?${params.toString()}`, { scroll: false });
    },
    [selected, maxSelect, router, searchParams]
  );

  if (models.length === 0) {
    return (
      <p className="font-mono text-xs text-muted">
        &gt; NO MODELS ON WATCHLIST.{" "}
        <a href="/watchlist" className="text-accent hover:underline">
          ADD MODELS
        </a>
      </p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {models.map((m) => {
        const active = selected.includes(m.model_id);
        return (
          <button
            key={m.model_id}
            type="button"
            onClick={() => toggle(m.model_id)}
            className={`font-mono text-xs px-3 py-1.5 border flex items-center gap-2 transition-colors ${
              active
                ? "border-accent text-accent bg-surface-elevated"
                : "border-border text-muted hover:border-accent/50"
            }`}
          >
            <ProviderLogo providerId={m.provider_id} size={16} />
            {m.display_name}
          </button>
        );
      })}
      <span className="font-mono text-[10px] text-muted self-center">
        {selected.length}/{maxSelect} selected
      </span>
    </div>
  );
}
