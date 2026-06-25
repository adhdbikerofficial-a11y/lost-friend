import * as Location from "expo-location";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import MapView, { Circle, Marker } from "react-native-maps";
import { useAuth } from "../../lib/auth";
import { API_URL } from "../../lib/api";
const A_CORUÑA = {
  latitude: 43.36,
  longitude: -8.41,
};

interface AlertaActiva {
  alerta_id: number;
  mascota_id: number;
  estado: string;
  radio_actual_km: number;
  lat: number;
  lon: number;
  descripcion: string | null;
  created_at: string;
  mascota_nombre: string;
  mascota_especie: string;
}

const MARKER_COLOR: Record<string, string> = {
  perro: "#dc2626",
  gato: "#2563eb",
  conejo: "#16a34a",
  ave: "#9333ea",
};

const getMarkerColor = (especie: string) => MARKER_COLOR[especie] ?? "#6b7280";
export default function MapaScreen() {
  const { token } = useAuth();
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertas, setAlertas] = useState<AlertaActiva[]>([]);
  const [alertasLoading, setAlertasLoading] = useState(true);
  const mapRef = useRef<MapView>(null);

  const fetchAlertas = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/alertas/activas`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setAlertas(await res.json());
      }
    } catch {
      // silencio — el mapa funciona aunque falle la carga
    } finally {
      setAlertasLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchAlertas();
  }, [fetchAlertas, token]);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setErrorMsg("Permiso de ubicación denegado");
        setLoading(false);
        return;
      }

      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setLocation(loc);
      setLoading(false);

      // Animamos el mapa a la ubicación actual
      mapRef.current?.animateToRegion(
        {
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        },
        1000
      );
    })();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1a1a2e" />
        <Text style={styles.loadingText}>Obteniendo ubicación...</Text>
      </View>
    );
  }

  const region = location
    ? {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 0.05,
        longitudeDelta: 0.05,
      }
    : {
        latitude: A_CORUÑA.latitude,
        longitude: A_CORUÑA.longitude,
        latitudeDelta: 0.1,
        longitudeDelta: 0.1,
      };

  const center = location
    ? {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      }
    : A_CORUÑA;

  return (
    <View style={styles.container}>
      <MapView ref={mapRef} style={styles.map} initialRegion={region}>
        {/* Círculo 1km */}
        <Circle
          center={center}
          radius={1000}
          strokeColor="rgba(220, 38, 38, 0.6)"
          fillColor="rgba(220, 38, 38, 0.1)"
          strokeWidth={2}
        />
        {/* Círculo 5km */}
        <Circle
          center={center}
          radius={5000}
          strokeColor="rgba(234, 179, 8, 0.5)"
          fillColor="rgba(234, 179, 8, 0.05)"
          strokeWidth={2}
        />
        {/* Círculo 10km */}
        <Circle
          center={center}
          radius={10000}
          strokeColor="rgba(59, 130, 246, 0.4)"
          fillColor="rgba(59, 130, 246, 0.03)"
          strokeWidth={2}
        />

        {/* Alertas activas — markers y círculos */}
        {alertas.map((a) => (
          <Marker
            key={`m-${a.alerta_id}`}
            coordinate={{ latitude: a.lat, longitude: a.lon }}
            title={`${a.mascota_nombre} — ${a.mascota_especie}`}
            description={`${a.estado} · radio ${a.radio_actual_km}km`}
            pinColor={getMarkerColor(a.mascota_especie)}
          />
        ))}
        {alertas.map((a) => (
          <Circle
            key={`c-${a.alerta_id}`}
            center={{ latitude: a.lat, longitude: a.lon }}
            radius={a.radio_actual_km * 1000}
            strokeColor="rgba(139, 92, 246, 0.5)"
            fillColor="rgba(139, 92, 246, 0.06)"
            strokeWidth={2}
          />
        ))}
      </MapView>

      {errorMsg && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      )}

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: "#dc2626" }]} />
          <Text style={styles.legendText}>1 km</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: "#eab308" }]} />
          <Text style={styles.legendText}>5 km</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: "#3b82f6" }]} />
          <Text style={styles.legendText}>10 km</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#E6F4FE",
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: "#666",
  },
  errorBanner: {
    position: "absolute",
    top: 60,
    left: 20,
    right: 20,
    backgroundColor: "rgba(0,0,0,0.75)",
    borderRadius: 10,
    padding: 12,
  },
  errorText: {
    color: "#fff",
    textAlign: "center",
    fontSize: 14,
  },
  legend: {
    position: "absolute",
    bottom: 100,
    right: 16,
    backgroundColor: "rgba(255,255,255,0.95)",
    borderRadius: 10,
    padding: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
    gap: 8,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    color: "#333",
  },
});
