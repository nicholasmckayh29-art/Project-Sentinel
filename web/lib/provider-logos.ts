const PROVIDER_DOMAINS: Record<string, string> = {
  openai: "openai.com",
  anthropic: "anthropic.com",
  google: "google.com",
  meta: "meta.com",
  mistral: "mistral.ai",
  cohere: "cohere.com",
  amazon: "amazon.com",
  microsoft: "microsoft.com",
};

export function providerLogoUrl(providerId: string): string {
  const domain = PROVIDER_DOMAINS[providerId.toLowerCase()] ?? `${providerId}.com`;
  return `https://logo.clearbit.com/${domain}`;
}
