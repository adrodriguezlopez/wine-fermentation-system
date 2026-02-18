# 🔍 Cómo Ver los Diagramas Mermaid

## 📊 Opción 1: Preview en VS Code (⭐ Recomendado)

**Lo más fácil y rápido:**

1. Abre cualquier archivo `.md` en VS Code
2. Presiona `Ctrl+Shift+V` (Windows/Linux) o `Cmd+Shift+V` (Mac)
3. ¡Los diagramas Mermaid se renderizan automáticamente!

![Preview en VS Code](./preview-vscode.png)

### Ventajas:
- ✅ Sin necesidad de instalar nada
- ✅ Preview en tiempo real mientras editas
- ✅ Puedes hacer zoom y click en los elementos
- ✅ Exporte a SVG/PNG desde el preview

---

## 🌐 Opción 2: Vista en GitHub

**Si los archivos están en un repositorio GitHub:**

1. Simplemente navega a cualquier archivo `.md`
2. GitHub renderiza automáticamente los diagramas Mermaid
3. ¡Listo! Sin instalar nada

### Ventajas:
- ✅ Accesible desde cualquier navegador
- ✅ Compartible con enlaces directos
- ✅ No requiere VS Code

---

## 💻 Opción 3: Extensión de VS Code (Para más características)

**Si quieres soporte extra para Mermaid:**

1. Abre Extensions en VS Code (`Ctrl+Shift+X`)
2. Busca "Mermaid"
3. Instala la extensión oficial `Mermaid.js`
4. Reinicia VS Code

### Características adicionales:
- 🎨 Tema personalizado
- 📥 Exportación a múltiples formatos
- 🔍 Búsqueda en diagramas
- ⌨️ Autocompletado de sintaxis

---

## 📱 Opción 4: Visor Online

**Si prefieres una herramienta online:**

1. Ve a https://mermaid.live
2. Copia el contenido del bloque ```mermaid```
3. Pégalo en el editor
4. El diagrama se renderiza al instante

### Ventajas:
- ✅ Funciona en cualquier dispositivo
- ✅ Sin instalaciones
- ✅ Exportación a SVG/PNG/PDF
- ✅ Compartir diagramas con links

---

## 🎯 Archivos con Diagramas

### Diagramas de Arquitectura
- **[01-GENERAL-ARCHITECTURE.md](./01-GENERAL-ARCHITECTURE.md)**
  - Sistema general (4 diagramas)
  - Componentes principales
  - Flujo de datos

### Diagramas de Componentes
- **[02-COMPONENTS.md](./02-COMPONENTS.md)**
  - Módulo Fermentation (4 diagramas)
  - Módulo Analysis Engine
  - Módulo Fruit Origin
  - Módulo Authentication

### Diagramas de Clases (NUEVO - Separado por componente)
- **[03-CLASS-DIAGRAMS.md](./03-CLASS-DIAGRAMS.md)**
  - Fermentation Module (6 entidades)
  - Analysis Engine Module (4 entidades)
  - Fruit Origin Module (4 entidades)
  - Authentication Module (1 entidad)
  - Winery Module (1 entidad)

### Diagramas de Secuencia
- **[04-SEQUENCE-DIAGRAMS.md](./04-SEQUENCE-DIAGRAMS.md)**
  - Create Fermentation
  - Add Sample
  - Analysis Workflow
  - Login Flow
  - Historical Comparison
  - Multi-Tenancy Isolation
  - Soft Delete Pattern

### Use Cases
- **[05-USE-CASES.md](./05-USE-CASES.md)**
  - UC-001 a UC-012
  - Error Scenarios

### Deployment & Infrastructure
- **[06-DEPLOYMENT-INFRASTRUCTURE.md](./06-DEPLOYMENT-INFRASTRUCTURE.md)**
  - Arquitectura Cloud
  - On-Premise
  - Schema de BD
  - Flujos de datos
  - Docker Compose
  - CI/CD Pipeline

---

## ❓ Preguntas Frecuentes

**P: ¿Los diagramas se renderizarán en mi editor?**  
R: Sí, siempre que sea un editor compatible con Markdown (VS Code, GitHub, etc.). Los diagramas están en formato texto Mermaid.

**P: ¿Puedo editar los diagramas?**  
R: Sí, simplemente edita el código Mermaid dentro de los bloques ` ```mermaid ``` ` y el preview se actualiza automáticamente.

**P: ¿Cómo exporto un diagrama a imagen?**  
R: 
- En VS Code: Haz clic derecho en el preview → "Export SVG" o "Export PNG"
- En GitHub: Haz clic en el diagrama → "Open in new tab" (se abre en mermaid.live)
- En mermaid.live: Usa el botón de descarga

**P: ¿Qué pasa si un diagrama no se renderiza?**  
R: Posibles causas:
1. Sintaxis Mermaid incorrecta (revisa los bloques ```)
2. Navegador desactualizado (actualiza tu navegador)
3. Cache: Intenta `Ctrl+Shift+R` para limpiar cache

---

## 🚀 Próximos Pasos

1. **Abre un diagrama ahora:**
   - [Diagrama de Arquitectura General](./01-GENERAL-ARCHITECTURE.md) 👈

2. **Para desarrolladores:**
   - [Diagramas de Clases por Componente](./03-CLASS-DIAGRAMS.md)
   - [Diagramas de Secuencia](./04-SEQUENCE-DIAGRAMS.md)

3. **Para arquitectos:**
   - [Arquitectura General](./01-GENERAL-ARCHITECTURE.md)
   - [Componentes](./02-COMPONENTS.md)
   - [Deployment](./06-DEPLOYMENT-INFRASTRUCTURE.md)

---

## 💡 Tips

- **Usa el Quick Reference:** [00-QUICK-REFERENCE.md](./00-QUICK-REFERENCE.md) para un índice visual
- **Búsqueda rápida:** `Ctrl+F` para buscar elementos en los diagramas
- **Zoom:** Usa `Ctrl + Scroll` en VS Code preview para hacer zoom
- **Pantalla completa:** F5 en el preview para una vista más grande

¡Disfruta explorando la arquitectura del sistema! 🎉
