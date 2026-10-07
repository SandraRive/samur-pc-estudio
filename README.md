# Manual SAMUR-PC · interactivo

Web de estudio del *Manual de Procedimientos SAMUR-Protección Civil 2026 v1.0*. Es un único HTML autónomo (`dist/index.html`): los datos van incrustados y funciona abriéndolo en el navegador.

## Estructura

```
src/template.html     Diseño + lógica de la web (CSS y JS). Aquí se hacen casi todos los cambios.
tools/tree.py         Árbol de ámbitos → bloques → procedimientos (título, página del PDF, nombre visible).
tools/build.py        Extrae del PDF el texto de cada procedimiento, el vademécum y las abreviaturas → data.json
tools/ref.py          Extrae claves de radio, códigos de incidente e indicativos → ref.json
tools/assemble.py     Inyecta data.json, ref.json e iconos Lucide en la plantilla → samur-manual.html
tools/screenshots.js  Capturas de prueba con Playwright (opcional)
data/data.json        Datos ya extraídos (procedimientos, fármacos, abreviaturas, árbol)
data/ref.json         Datos ya extraídos (claves, códigos, indicativos)
dist/index.html       La web final
build.sh              Script de compilación
```

## Requisitos
- Python 3
- Node + npm (solo para los iconos `lucide-static`)
- `pdftotext` (paquete poppler-utils) si vas a re-extraer del PDF

## Compilar

```bash
npm install
./build.sh                      # re-ensambla con los datos de data/ (para cambios de diseño)
./build.sh ManualSAMUR2026.pdf  # vuelve a extraer todo del PDF (nueva versión del manual)
```

## Cómo cambiar cosas
- **Diseño, colores, textos de la web, quiz, chuletas** → `src/template.html`.
  - Colores por ámbito: objeto `COL` en el JS.
  - Rangos de XP: `RANKS`. Modos de reto: `MODES`. Chuletas: función `vRepaso`.
- **Mover un procedimiento de bloque o renombrarlo** → `tools/tree.py` y recompilar con el PDF.
- **Iconos**: nombres de [Lucide](https://lucide.dev/icons). Si usas uno nuevo, añádelo a la lista `need` de `assemble.py`.

## Datos guardados
El progreso (estudiados, XP, récords) se guarda en `localStorage` con la clave `samurpc-v1`, solo en ese navegador.

## Limitaciones conocidas
- Los diagramas y algoritmos gráficos del PDF no se extraen (cada procedimiento indica sus páginas).
- Algunas tablas salen en formato texto original.

## Publicación
Cada push a `main` compila la web y la publica en GitHub Pages (workflow `.github/workflows/pages.yml`).
Actívalo una vez en *Settings → Pages → Source: GitHub Actions*.

## Aviso
Proyecto personal de estudio. El contenido procede del Manual de Procedimientos de SAMUR-Protección Civil (Ayuntamiento de Madrid); no es una publicación oficial. El PDF original no se incluye en el repositorio.
