import * as Location from "expo-location";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { WebView } from "react-native-webview";
import type { WebViewMessageEvent } from "react-native-webview";
import { useAuth } from "../../lib/auth";
import { API_URL } from "../../lib/api";
import {
  borderRadius,
  colors,
  fontSize,
  getMarkerColor,
  MARKER_COLOR,
  shadow,
} from "../../lib/theme";

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

// Plantilla HTML con Leaflet + LocationIQ, se inyecta directo en el WebView
// para evitar problemas de assets en Expo managed workflow.
// La API key se inyecta como parámetro en vez de estar hardcodeada.
const getMapHtml = (apiKey: string) => String.raw`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <title>Lost Friend Map</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body, #map { width: 100%; height: 100%; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    (function () {
      "use strict";

      var map = L.map("map", {
        center: [43.36, -8.41],
        zoom: 13,
        zoomControl: true,
      });

      L.tileLayer(
        "https://tiles.locationiq.com/v3/streets/r/{z}/{x}/{y}.png?key=${apiKey}",
        {
          attribution:
            '&copy; <a href="https://www.locationiq.com/">LocationIQ</a>',
          maxZoom: 18,
        }
      ).addTo(map);

      var circles = {};
      var markers = {};

      function parseRgbaAlpha(color) {
        if (!color || typeof color !== "string") return null;
        var match = color.match(
          /rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)/
        );
        if (match) return parseFloat(match[4]);
        return null;
      }

      function stripAlpha(color) {
        if (!color || typeof color !== "string") return color || "#3388ff";
        var match = color.match(
          /rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)/
        );
        if (match) return "rgb(" + match[1] + ", " + match[2] + ", " + match[3] + ")";
        return color;
      }

      window.addEventListener("message", function (event) {
        try {
          var data = JSON.parse(event.data);
        } catch (e) {
          return;
        }

        switch (data.type) {
          case "setCenter":
            map.setView([data.lat, data.lng], 13);
            break;

          case "flyTo":
            map.flyTo([data.lat, data.lng], 13, { duration: 1 });
            break;

          case "addCircles":
            if (data.circles) {
              data.circles.forEach(function (c) {
                if (circles[c.id]) {
                  map.removeLayer(circles[c.id]);
                }
                var fillColor = stripAlpha(c.fillColor || c.color || "#3388ff");
                var alpha = parseRgbaAlpha(c.fillColor || "");
                var fillOpacity = alpha !== null ? alpha : 0.1;
                var circle = L.circle([c.lat, c.lng], {
                  radius: c.radiusKm * 1000,
                  color: c.strokeColor || c.color || "#3388ff",
                  fillColor: fillColor,
                  fillOpacity: fillOpacity,
                  weight: c.weight || 2,
                }).addTo(map);
                circles[c.id] = circle;
              });
            }
            break;

          case "addMarkers":
            if (data.markers) {
              data.markers.forEach(function (m) {
                if (markers[m.id]) {
                  map.removeLayer(markers[m.id]);
                }
                var marker = L.circleMarker([m.lat, m.lng], {
                  radius: 8,
                  color: m.color || "#3388ff",
                  fillColor: m.color || "#3388ff",
                  fillOpacity: 0.8,
                  weight: 2,
                }).addTo(map);
                if (m.title) {
                  var popupHtml = "<b>" + m.title + "</b>";
                  if (m.description) {
                    popupHtml += "<br/>" + m.description;
                  }
                  marker.bindPopup(popupHtml);
                }
                markers[m.id] = marker;
              });
            }
            break;

          case "clearCircles":
            Object.keys(circles).forEach(function (id) {
              map.removeLayer(circles[id]);
            });
            circles = {};
            break;

          case "clearMarkers":
            Object.keys(markers).forEach(function (id) {
              map.removeLayer(markers[id]);
            });
            markers = {};
            break;

          case "clearAll":
            Object.keys(circles).forEach(function (id) {
              map.removeLayer(circles[id]);
            });
            Object.keys(markers).forEach(function (id) {
              map.removeLayer(markers[id]);
            });
            circles = {};
            markers = {};
            break;

          case "setMapZoom":
            map.setZoom(data.zoom);
            break;
        }
      });

      // Notify React Native that the map is ready
      if (window.ReactNativeWebView && window.ReactNativeWebView.postMessage) {
        window.ReactNativeWebView.postMessage(
          JSON.stringify({ type: "mapReady" })
        );
      }
    })();
  </script>
</body>
</html>`;

export default function MapaScreen() {
  const { token } = useAuth();
  const [location, setLocation] = useState<Location.LocationObject | null>(
    null,
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [alertas, setAlertas] = useState<AlertaActiva[]>([]);
  const [alertasLoading, setAlertasLoading] = useState(true);
  const webViewRef = useRef<WebView>(null);
  const [mapReady, setMapReady] = useState(false);

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
    })();
  }, []);

  // Envía datos al WebView cuando el mapa está listo y tenemos ubicación/alertas
  useEffect(() => {
    if (!mapReady || !webViewRef.current) return;

    const lat = location?.coords.latitude ?? A_CORUÑA.latitude;
    const lng = location?.coords.longitude ?? A_CORUÑA.longitude;

    // Volar a la ubicación del usuario
    webViewRef.current.postMessage(
      JSON.stringify({ type: "flyTo", lat, lng }),
    );

    // Limpiar capas previas
    webViewRef.current.postMessage(JSON.stringify({ type: "clearAll" }));

    // Círculos de expansión centrados en el usuario
    const expansionCircles = [
      {
        id: "user-1km",
        lat,
        lng,
        radiusKm: 1,
        color: colors.mapRadius1km,
        fillColor: "rgba(220, 38, 38, 0.1)",
      },
      {
        id: "user-5km",
        lat,
        lng,
        radiusKm: 5,
        color: colors.mapRadius5km,
        fillColor: "rgba(234, 179, 8, 0.05)",
      },
      {
        id: "user-10km",
        lat,
        lng,
        radiusKm: 10,
        color: colors.mapRadius10km,
        fillColor: "rgba(59, 130, 246, 0.03)",
      },
    ];
    webViewRef.current.postMessage(
      JSON.stringify({ type: "addCircles", circles: expansionCircles }),
    );

    // Marcadores y círculos de alertas activas
    if (alertas.length > 0) {
      const markers = alertas.map((a) => ({
        id: `m-${a.alerta_id}`,
        lat: a.lat,
        lng: a.lon,
        title: `${a.mascota_nombre} — ${a.mascota_especie}`,
        description: `${a.estado} · radio ${a.radio_actual_km}km`,
        color: getMarkerColor(a.mascota_especie),
      }));
      const alertCircles = alertas.map((a) => ({
        id: `c-${a.alerta_id}`,
        lat: a.lat,
        lng: a.lon,
        radiusKm: a.radio_actual_km,
        color: colors.mapAlert,
        fillColor: colors.mapAlertFill,
      }));

      webViewRef.current.postMessage(
        JSON.stringify({ type: "addMarkers", markers }),
      );
      webViewRef.current.postMessage(
        JSON.stringify({ type: "addCircles", circles: alertCircles }),
      );
    }
  }, [mapReady, location, alertas]);

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === "mapReady") {
        setMapReady(true);
      }
    } catch {
      // ignorar mensajes malformados
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Obteniendo ubicación...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <WebView
        ref={webViewRef}
        source={{ html: getMapHtml(process.env.EXPO_PUBLIC_LOCATIONIQ_KEY ?? "") }}
        style={styles.map}
        onMessage={handleMessage}
        javaScriptEnabled
        domStorageEnabled
        originWhitelist={["*"]}
      />

      {errorMsg && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      )}

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.mapRadius1km }]} />
          <Text style={styles.legendText}>1 km</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.mapRadius5km }]} />
          <Text style={styles.legendText}>5 km</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.mapRadius10km }]} />
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
    backgroundColor: colors.bg,
  },
  loadingText: {
    marginTop: 12,
    fontSize: fontSize.sm,
    color: colors.textLight,
  },
  errorBanner: {
    position: "absolute",
    top: 60,
    left: 20,
    right: 20,
    backgroundColor: colors.bgOverlay,
    borderRadius: borderRadius.md,
    padding: 12,
  },
  errorText: {
    color: colors.textWhite,
    textAlign: "center",
    fontSize: fontSize.sm,
  },
  legend: {
    position: "absolute",
    bottom: 100,
    right: 16,
    backgroundColor: "rgba(255,255,255,0.95)",
    borderRadius: borderRadius.md,
    padding: 12,
    ...shadow.card,
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
    fontSize: fontSize.xs,
    color: colors.text,
  },
});
