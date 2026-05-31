/** Shared Mr. Robot / terminal design tokens — web + future mobile */

export const theme = {
  colors: {
    background: "#0D0D0D",
    surface: "#111111",
    surfaceElevated: "#1A1A1A",
    border: "#2A2A2A",
    text: "#E0E0E0",
    textMuted: "#888888",
    accent: "#00FF41",
    accentDim: "#00AA2A",
    alertDrop: "#00FF41",
    alertIncrease: "#FF3333",
    warning: "#FFB800",
  },
  fonts: {
    mono: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace",
    sans: "system-ui, -apple-system, sans-serif",
  },
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
} as const;

export type Theme = typeof theme;
