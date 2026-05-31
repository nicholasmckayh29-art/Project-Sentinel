"use client";

import { providerLogoUrl } from "@/lib/provider-logos";

export function ProviderLogo({
  providerId,
  size = 20,
}: {
  providerId: string;
  size?: number;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={providerLogoUrl(providerId)}
      alt=""
      width={size}
      height={size}
      className="rounded-sm object-contain bg-surface-elevated"
      onError={(e) => {
        (e.target as HTMLImageElement).style.display = "none";
      }}
    />
  );
}
