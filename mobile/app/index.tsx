import { router } from "expo-router";
import { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";
import { useAuth } from "../lib/auth";

/**
 * Pantalla de entrada — redirige según estado de auth.
 * Si hay token guardado → (main), si no → /login.
 */
export default function Index() {
  const { token, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    router.replace(token ? "/(main)" : "/login");
  }, [token, isLoading]);

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <ActivityIndicator size="large" />
    </View>
  );
}
