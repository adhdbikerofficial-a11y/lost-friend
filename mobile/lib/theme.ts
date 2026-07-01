/** Tokens de diseño de Lost Friend — tema oscuro consistente. */

export const colors = {
  // Brand
  primary: "#1a1a2e",
  primaryLight: "#16213e",
  accent: "#0f3460",

  // Backgrounds
  bg: "#E6F4FE",
  bgCard: "#fff",
  bgOverlay: "rgba(0,0,0,0.75)",

  // Text
  text: "#333",
  textLight: "#666",
  textWhite: "#fff",
  textTitle: "#1a1a2e",

  // Status
  error: "#dc2626",
  success: "#16a34a",
  warning: "#eab308",
  info: "#3b82f6",

  // Map
  mapRadius1km: "#dc2626",
  mapRadius5km: "#eab308",
  mapRadius10km: "#3b82f6",
  mapAlert: "#8b5cf6",
  mapAlertFill: "rgba(139, 92, 246, 0.06)",

  // Species markers
  perro: "#dc2626",
  gato: "#2563eb",
  conejo: "#16a34a",
  ave: "#9333ea",
  defaultMarker: "#6b7280",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
} as const;

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  full: 9999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 22,
  xxl: 28,
} as const;

export const shadow = {
  card: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
} as const;

export const MARKER_COLOR: Record<string, string> = {
  perro: colors.perro,
  gato: colors.gato,
  conejo: colors.conejo,
  ave: colors.ave,
};

export const getMarkerColor = (especie: string): string =>
  MARKER_COLOR[especie] ?? colors.defaultMarker;
