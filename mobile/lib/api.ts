/**
 * Configuración centralizada de la URL base de la API.
 *
 * Prioridad:
 * 1. `EXPO_PUBLIC_API_URL` — variable de entorno en EAS Build (producción)
 * 2. IP local — desarrollo local con Expo Go
 *
 * En EAS Build, seteá: EXPO_PUBLIC_API_URL=https://tudominio.railway.app
 * Para emulador Android, usá: http://10.0.2.2:8000
 */
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL || "http://192.168.0.25:8000";
