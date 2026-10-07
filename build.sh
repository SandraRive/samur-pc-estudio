#!/usr/bin/env bash
# Regenera dist/index.html a partir del PDF del manual.
# Uso: ./build.sh ruta/al/ManualSAMUR.pdf   (sin argumento, solo re-ensambla con los datos ya extraídos)
set -e
cd "$(dirname "$0")"
mkdir -p work
cp src/template.html work/
cp tools/*.py work/
if [ -n "$1" ]; then
  cp "$1" work/m.pdf
  (cd work && pdftotext -layout m.pdf L.txt && python3 build.py && python3 ref.py)
  cp work/data.json work/ref.json data/
else
  cp data/data.json data/ref.json work/
fi
[ -d node_modules/lucide-static ] || npm install
ln -sfn ../node_modules work/node_modules
(cd work && python3 assemble.py)
cp work/samur-manual.html dist/index.html
echo "OK -> dist/index.html"
