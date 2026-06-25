import { router, Tabs } from "expo-router";
import { useEffect } from "react";
import { ActivityIndicator, Pressable, Text, View } from "react-native";
import { useAuth } from "../../lib/auth";

/**
 * Layout protegido con tabs — redirige a /login si no hay token.
 */
export default function MainLayout() {
  const { token, isLoading, clearToken } = useAuth();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [token, isLoading]);

  const handleLogout = async () => {
    await clearToken();
    router.replace("/login");
  };

  if (isLoading || !token) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: "#1a1a2e" },
        headerTintColor: "#fff",
        headerTitleStyle: { fontWeight: "700" },
        headerRight: () => (
          <Pressable
            onPress={handleLogout}
            style={{ marginRight: 16, paddingHorizontal: 10, paddingVertical: 4 }}
          >
            <Text style={{ color: "#fff", fontSize: 14 }}>Salir</Text>
          </Pressable>
        ),
        tabBarActiveTintColor: "#1a1a2e",
        tabBarInactiveTintColor: "#999",
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Alerta",
          headerTitle: "Lost Friend",
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 20, color }}>🚨</Text>
          ),
        }}
      />
      <Tabs.Screen
        name="mapa"
        options={{
          title: "Mapa",
          headerTitle: "Mapa de alertas",
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 20, color }}>🗺️</Text>
          ),
        }}
      />
    </Tabs>
  );
}
