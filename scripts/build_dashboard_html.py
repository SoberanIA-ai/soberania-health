"""Build del dashboard HTML conectado a la API.

Toma el HTML de Claude Design original (con datos demo), reemplaza los
dos assets clave del manifest:
  - dc0dda47…  (datos seed con window.SOBERANIA_DATA) → vacío
  - 40c45379…  (código React App) → versión que hace fetch a la API

Recomprime ambos con gzip + base64 y reescribe el HTML modificado.

Uso:
    python scripts/build_dashboard_html.py

Lee:
    dashboard/hitl_dashboard.html.original  (HTML de Claude Design)
    dashboard/_app_live.js                  (App.js con fetch real)

Escribe:
    dashboard/hitl_dashboard.html           (HTML conectado a la API)

Idempotente — se puede correr cada vez que se cambia _app_live.js.
"""
import base64
import gzip
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ORIGINAL = REPO / "dashboard" / "hitl_dashboard.html.original"
APP_LIVE = REPO / "dashboard" / "_app_live.js"
DESTINO = REPO / "dashboard" / "hitl_dashboard.html"

UUID_APP = "40c45379-901d-4807-b8de-75e9009f24a6"
UUID_SEED = "dc0dda47-081d-4fc6-a04c-1a3b37f22d9d"

SEED_VACIO = (
    "// Seed vacío — el App live hace fetch a la API en cada refresh.\n"
    "window.SOBERANIA_DATA = { metrics: { procesadas: 0, automatizadas: 0, "
    "pendientes: 0, tiempoMedio: 0 }, cola: [] };\n"
)


def _encode_asset(texto: str, compressed: bool = True) -> str:
    raw = texto.encode("utf-8")
    if compressed:
        raw = gzip.compress(raw)
    return base64.b64encode(raw).decode("ascii")


def main() -> None:
    if not ORIGINAL.exists():
        raise SystemExit(f"No encuentro {ORIGINAL}")
    if not APP_LIVE.exists():
        raise SystemExit(f"No encuentro {APP_LIVE}")

    print(f"Leyendo {ORIGINAL.name}...")
    lines = ORIGINAL.read_text(encoding="utf-8").splitlines(keepends=True)

    # Buscar la línea con el manifest JSON. Está justo después del tag
    # <script type="__bundler/manifest"> (sin contar líneas dentro de strings JS).
    manifest_line_idx = None
    for i, line in enumerate(lines):
        # El TAG abre una línea, el JSON está en la siguiente
        stripped = line.strip()
        if stripped.startswith('<script') and 'type="__bundler/manifest"' in stripped:
            manifest_line_idx = i + 1
            break
    if manifest_line_idx is None:
        raise SystemExit("No encuentro el manifest del bundler en el HTML")

    print(f"Manifest en línea {manifest_line_idx + 1}, decodificando...")
    manifest = json.loads(lines[manifest_line_idx])
    print(f"  {len(manifest)} assets en el manifest")

    if UUID_APP not in manifest:
        raise SystemExit(f"No encuentro asset App ({UUID_APP}) en el manifest")
    if UUID_SEED not in manifest:
        raise SystemExit(f"No encuentro asset seed ({UUID_SEED}) en el manifest")

    app_js = APP_LIVE.read_text(encoding="utf-8")
    print(f"Reemplazando asset App con _app_live.js ({len(app_js)} chars)...")
    manifest[UUID_APP]["data"] = _encode_asset(app_js, compressed=True)
    manifest[UUID_APP]["compressed"] = True

    print(f"Vaciando seed data ({len(SEED_VACIO)} chars)...")
    manifest[UUID_SEED]["data"] = _encode_asset(SEED_VACIO, compressed=True)
    manifest[UUID_SEED]["compressed"] = True

    print("Reescribiendo manifest en el HTML...")
    lines[manifest_line_idx] = json.dumps(manifest, separators=(",", ":")) + "\n"

    DESTINO.write_text("".join(lines), encoding="utf-8")
    size_mb = DESTINO.stat().st_size / 1024 / 1024
    print(f"✓ Escrito {DESTINO.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
