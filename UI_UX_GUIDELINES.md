\# UI\_UX\_GUIDELINES.md \- Lost Friend MVP

\#\# 1\. Core Aesthetic & Design Philosophy  
\- \*\*Estilo Principal:\*\* Premium Minimalism / "Apple-style" / Cyber-Luxe.  
\- \*\*Tema por Defecto:\*\* Dark Mode estricto. Reduce la fatiga visual de las autoridades en el dashboard y resalta los elementos de emergencia (alertas) por contraste.  
\- \*\*Atmósfera:\*\* Interfaces limpias, estructuradas y sin saturación de información. El uso del espacio en blanco (o espacio oscuro) es fundamental para guiar la vista del usuario en momentos de estrés.

\#\# 2\. Paleta de Colores  
\- \*\*Background Principal:\*\* \`\#0A0A0C\` (Negro profundo, casi OLED).  
\- \*\*Superficies / Tarjetas:\*\* \`\#1C1C1E\` o fondos translúcidos usando Glassmorphism (\`rgba(255, 255, 255, 0.05)\` con blur).  
\- \*\*Acento Primario (Acciones seguras):\*\* \`\#0A84FF\` (Azul vibrante, estilo iOS).  
\- \*\*Acento Peligro / Alerta (Botón de pánico, círculos 1-5-10km):\*\* \`\#FF3B30\` (Rojo emergencia, alta visibilidad).  
\- \*\*Acento Éxito (Hallazgo / Resolución):\*\* \`\#32D74B\` (Verde brillante).  
\- \*\*Texto Principal:\*\* \`\#F2F2F7\` (Blanco con ligera opacidad para no deslumbrar).  
\- \*\*Texto Secundario:\*\* \`\#EBEBF5\` (Gris claro al 60% de opacidad).

\#\# 3\. Tipografía  
\- \*\*Familia:\*\* Inter, SF Pro, o Roboto (fuentes geométricas sans-serif puras).  
\- \*\*Jerarquía:\*\*  
  \- \`H1\` (Títulos de pantalla): 28px \- 32px, Font-Weight: 700 (Bold).  
  \- \`H2\` (Subtítulos / Nombres de mascotas): 20px \- 24px, Font-Weight: 600 (Semi-bold).  
  \- \`Body\` (Texto descriptivo): 16px, Font-Weight: 400 (Regular).  
  \- \`Micro\` (Etiquetas, fechas, radios de mapa): 12px, Font-Weight: 500 (Medium).

\#\# 4\. Componentes y Efectos (Directivas de Construcción)  
\- \[cite\_start\]\*\*Glassmorphism (Efecto Cristal):\*\* Obligatorio para modales de confirmación (ej. ingreso de clave única), barras de navegación y tarjetas flotantes sobre mapas.  
  \- \*Web (Next.js):\* Usar \`backdrop-blur-md\`, fondos \`bg-white/5\` y bordes sutiles \`border border-white/10\`.  
  \- \*Mobile (React Native):\* Usar librerías como \`expo-blur\`.  
\- \*\*Bordes y Esquinas:\*\* Generosos. Usar radios de borde de \`16px\` o \`24px\` (\`rounded-2xl\` o \`rounded-3xl\` en Tailwind) para tarjetas y botones. No usar bordes afilados.  
\- \*\*Botón de Pánico:\*\* Debe ser el elemento visualmente más pesado de la pantalla inicial. Recomendar animaciones de "pulso" (pulse effect) sutiles y, en móvil, implementar respuesta háptica (Haptic Feedback) al presionarlo.

\#\# 5\. Mapas y Círculos de Alerta (Core Geoespacial)  
\- \*\*Estilo de Mapa:\*\* Usar temas oscuros estandarizados para mapas (ej. Dark mode de Google Maps o Mapbox). Calles en gris muy oscuro, agua en negro azulado.  
\- \*\*Radios de Alerta:\*\*  
  \- 1 km: Círculo rojo \`\#FF3B30\` con relleno translúcido al 20%.  
  \- 5 km: Círculo naranja brillante con relleno translúcido al 15%.  
  \- 10 km: Círculo amarillo con relleno translúcido al 10%.

\#\# 6\. Prohibiciones Visuales para la IA  
\- PROHIBIDO usar componentes genéricos tipo Bootstrap.  
\- PROHIBIDO usar sombras duras (drop-shadows opacas). Usar sombras difusas (\`box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37)\`).  
\- PROHIBIDO el uso de múltiples fuentes tipográficas. Limitarse a una sola familia variando el grosor y el tamaño.  
