import * as Location from "expo-location";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useAuth } from "../../lib/auth";
import { API_URL } from "../../lib/api";

const ESPECIES = ["perro", "gato", "conejo", "ave", "otro"] as const;

interface Mascota {
  id: number;
  nombre: string;
  especie: string;
  raza: string | null;
  color: string | null;
  codigo_emergencia: string;
}

/**
 * Pantalla principal — botón de pánico con selector de mascota registrada.
 *
 * Si el usuario ya registró mascotas, las muestra para selección rápida.
 * También permite crear una alerta con datos nuevos manualmente.
 */
export default function PanicButtonScreen() {
  const { token } = useAuth();

  // Mascotas del usuario
  const [mascotas, setMascotas] = useState<Mascota[]>([]);
  const [mascotasLoading, setMascotasLoading] = useState(true);

  // Formulario manual
  const [nombre, setNombre] = useState("");
  const [especie, setEspecie] = useState<string>("perro");
  const [raza, setRaza] = useState("");
  const [showEspecies, setShowEspecies] = useState(false);

  // Estado general
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [locationError, setLocationError] = useState(false);

  /** Obtiene ubicación al montar */
  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setLocationError(true);
        return;
      }
      const loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      setLocation(loc);
    })();
  }, []);

  /** Obtiene mascotas del usuario */
  const fetchMascotas = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/mascotas`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: Mascota[] = await res.json();
        setMascotas(data);
      }
    } catch {
      // Silencio — si falla, mostramos solo el formulario manual
    } finally {
      setMascotasLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchMascotas();
  }, [fetchMascotas]);

  /** Selecciona una mascota registrada — auto-completa el formulario */
  const seleccionarMascota = (m: Mascota) => {
    setNombre(m.nombre);
    setEspecie(m.especie);
    setRaza(m.raza ?? "");
  };

  const handlePanic = async () => {
    if (!nombre.trim()) {
      Alert.alert("Error", "Decinos el nombre de tu mascota");
      return;
    }

    if (!location) {
      Alert.alert(
        "Ubicación",
        locationError
          ? "Permiso de ubicación denegado. Activá el GPS en ajustes."
          : "Obteniendo ubicación... Esperá un segundo y volvé a intentar."
      );
      return;
    }

    setLoading(true);
    try {
      const lat = location.coords.latitude;
      const lon = location.coords.longitude;

      const res = await fetch(`${API_URL}/alertas`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          mascota: {
            nombre: nombre.trim(),
            especie,
            raza: raza.trim() || undefined,
          },
          ubicacion: { lat, lon },
          descripcion: `Se perdió ${nombre} (${especie})`,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        Alert.alert("Error", err.detail || "No se pudo crear la alerta");
        return;
      }

      const data = await res.json();
      Alert.alert(
        "🚨 ¡Alerta creada!",
        [
          `Código de emergencia: ${data.codigo_emergencia}`,
          `Radio inicial: ${data.radio_actual_km}km`,
          "",
          "Compartí este código con quien te ayude a buscar.",
          "La alerta se expandirá: 1km → 5km → 10km",
        ].join("\n"),
        [{ text: "OK" }]
      );
    } catch {
      Alert.alert("Error", "No se pudo conectar con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>¿Perdiste tu mascota?</Text>
        <Text style={styles.subtitle}>
          Seleccioná una de tus mascotas o ingresá los datos manualmente
        </Text>

        {/* Selector de mascotas registradas */}
        {mascotasLoading ? (
          <ActivityIndicator
            size="small"
            color="#1a1a2e"
            style={{ marginBottom: 20 }}
          />
        ) : mascotas.length > 0 ? (
          <View style={styles.petList}>
            <Text style={styles.sectionLabel}>Tus mascotas</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ gap: 10 }}
            >
              {mascotas.map((m) => {
                const selected =
                  nombre === m.nombre && especie === m.especie;
                return (
                  <Pressable
                    key={m.id}
                    style={[
                      styles.petChip,
                      selected && styles.petChipActive,
                    ]}
                    onPress={() => seleccionarMascota(m)}
                  >
                    <Text
                      style={[
                        styles.petChipEmoji,
                        selected && styles.petChipEmojiActive,
                      ]}
                    >
                      {m.especie === "perro"
                        ? "🐕"
                        : m.especie === "gato"
                          ? "🐱"
                          : m.especie === "conejo"
                            ? "🐰"
                            : m.especie === "ave"
                              ? "🐦"
                              : "🐾"}
                    </Text>
                    <Text
                      style={[
                        styles.petChipName,
                        selected && styles.petChipNameActive,
                      ]}
                    >
                      {m.nombre}
                    </Text>
                    <Text
                      style={[
                        styles.petChipDetail,
                        selected && styles.petChipDetailActive,
                      ]}
                    >
                      {m.especie}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        ) : null}

        {/* Línea divisoria si hay mascotas */}
        {mascotas.length > 0 && (
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>o ingresá manualmente</Text>
            <View style={styles.dividerLine} />
          </View>
        )}

        {/* Formulario manual */}
        <TextInput
          style={styles.input}
          placeholder="Nombre de tu mascota"
          placeholderTextColor="#999"
          value={nombre}
          onChangeText={setNombre}
        />

        <Pressable
          style={styles.selector}
          onPress={() => setShowEspecies(!showEspecies)}
        >
          <Text style={styles.selectorText}>
            {especie.charAt(0).toUpperCase() + especie.slice(1)}
          </Text>
          <Text style={styles.selectorArrow}>
            {showEspecies ? "▲" : "▼"}
          </Text>
        </Pressable>

        {showEspecies && (
          <View style={styles.dropdown}>
            {ESPECIES.map((esp) => (
              <Pressable
                key={esp}
                style={[
                  styles.dropdownItem,
                  especie === esp && styles.dropdownItemActive,
                ]}
                onPress={() => {
                  setEspecie(esp);
                  setShowEspecies(false);
                }}
              >
                <Text
                  style={[
                    styles.dropdownItemText,
                    especie === esp && styles.dropdownItemTextActive,
                  ]}
                >
                  {esp.charAt(0).toUpperCase() + esp.slice(1)}
                </Text>
              </Pressable>
            ))}
          </View>
        )}

        <TextInput
          style={styles.input}
          placeholder="Raza (opcional)"
          placeholderTextColor="#999"
          value={raza}
          onChangeText={setRaza}
        />

        <Pressable
          style={[styles.panicButton, loading && styles.panicButtonDisabled]}
          onPress={handlePanic}
          disabled={loading}
        >
          <Text style={styles.panicButtonText}>
            {loading ? "CREANDO ALERTA..." : "🚨 ALERTA"}
          </Text>
        </Pressable>

        <Text style={styles.hint}>
          Se notificará a usuarios en 1km a la redonda.{"\n"}
          La alerta se expandirá: 1km → 5km → 10km
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#E6F4FE",
  },
  content: {
    flexGrow: 1,
    alignItems: "center",
    padding: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1a1a2e",
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    marginBottom: 24,
    lineHeight: 20,
  },
  // Selector de mascotas
  petList: {
    width: "100%",
    marginBottom: 8,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#999",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 10,
  },
  petChip: {
    backgroundColor: "#fff",
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    alignItems: "center",
    minWidth: 90,
    borderWidth: 2,
    borderColor: "#eee",
  },
  petChipActive: {
    borderColor: "#1a1a2e",
    backgroundColor: "#f0f4ff",
  },
  petChipEmoji: {
    fontSize: 28,
    marginBottom: 4,
  },
  petChipEmojiActive: {},
  petChipName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  petChipNameActive: {
    color: "#1a1a2e",
  },
  petChipDetail: {
    fontSize: 11,
    color: "#999",
    marginTop: 2,
  },
  petChipDetailActive: {
    color: "#666",
  },
  // Divisoria
  divider: {
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
    marginVertical: 16,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: "#ddd",
  },
  dividerText: {
    marginHorizontal: 12,
    fontSize: 12,
    color: "#999",
  },
  // Formulario
  input: {
    width: "100%",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    backgroundColor: "#fff",
    marginBottom: 12,
  },
  selector: {
    width: "100%",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 14,
    backgroundColor: "#fff",
    marginBottom: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  selectorText: {
    fontSize: 16,
    color: "#1a1a2e",
  },
  selectorArrow: {
    fontSize: 12,
    color: "#999",
  },
  dropdown: {
    width: "100%",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    backgroundColor: "#fff",
    marginBottom: 12,
    overflow: "hidden",
  },
  dropdownItem: {
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  dropdownItemActive: {
    backgroundColor: "#E6F4FE",
  },
  dropdownItemText: {
    fontSize: 16,
    color: "#333",
  },
  dropdownItemTextActive: {
    color: "#1a1a2e",
    fontWeight: "600",
  },
  panicButton: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: "#dc2626",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#dc2626",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
    marginTop: 12,
  },
  panicButtonDisabled: {
    opacity: 0.6,
  },
  panicButtonText: {
    color: "#fff",
    fontSize: 24,
    fontWeight: "800",
    textAlign: "center",
  },
  hint: {
    marginTop: 32,
    fontSize: 12,
    color: "#999",
    textAlign: "center",
    lineHeight: 18,
  },
});
