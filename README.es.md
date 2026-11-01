# radar-pautas

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 Español**

## Qué es

radar-pautas es un script que lee, de una sola vez, unos 20 sitios de noticias sobre inteligencia artificial (blogs de empresas, prensa, Hacker News, Reddit y los proyectos que más estrellas ganaron en GitHub durante la semana) y devuelve los 6 temas más candentes de las últimas 24 horas. Sirve para quienes producen contenido y necesitan decidir rápidamente el tema del día. Reúne la misma noticia publicada en varios sitios, le asigna una puntuación, comprueba si el enlace funciona, avisa si ya hiciste algo parecido y, si lo pides, sugiere un titular, un gancho y un formato en portugués. Necesita Python 3; GitHub CLI (`gh`) y Claude Code son opcionales.

## Usar

```bash
git clone https://github.com/inematds/radar-pautas ~/projetos/radar-pautas
cd ~/projetos/radar-pautas
python3 radar.py --dry          # ver los 6 temas sin guardar
python3 radar.py --angulos      # guardar + titular/gancho/formato en PT (Claude Code)
```

Abre `~/projetos/output/radar-pautas/<data>/radar.html` en el navegador.

| Opción | Hace |
|---|---|
| `--horas 48` | período de tiempo (predeterminado: 24) |
| `--n 8` | cuántos temas (predeterminado: 6) |
| `--angulos` | titular, por qué importa, gancho, formato y palabra, mediante `claude -p` (suscripción) |
| `--sem-github` | sin los repositorios en tendencia |
| `--dry` | solo imprime |

## El proceso, de principio a fin

🧠 sesión con Nei · ⚙️ script/timer · 🤖 `claude -p` (suscripción)

| # | Paso | Comando / qué sucede | Quién |
|---|---|---|---|
| 1 | Recopilación | `radar.py` lee en paralelo los feeds de `fontes.json` (y vuelve a intentarlo cuando el sitio pide que esperes) + `gh search repos` | ⚙️ |
| 2 | Agrupa y puntúa | la misma noticia en varios sitios se convierte en un tema; puntuación según las fuentes, actualidad y fuente oficial | ⚙️ |
| 3 | Comprueba | abre el enlace de cada tema (solo se incluye con un 200) y busca algo parecido en `PRODUCOES-VIDEO.md` | ⚙️ |
| 4 | Ángulo | `--angulos`: titular PT, gancho, formato (r7ex/explicavideo/carrossel) y palabra | 🤖 |
| 5 | Elección | Nei elige qué temas se convertirán en video o carrusel | 🧠 |
| 6 | Informe diario (opcional) | `systemd/radar-pautas.timer` a las 07:30 — **viene desactivado**; activarlo solo con autorización | ⚙️ |

## Fuentes

`fontes.json`: OpenAI, Google AI, Google DeepMind, Hugging Face, NVIDIA, Mistral, GitHub Blog, The Verge, TechCrunch, Ars Technica, Wired, The Decoder, MarkTechPost, MIT News, Simon Willison, Hacker News (más de 150 puntos), r/LocalLLaMA, Tecmundo, Canaltech y Olhar Digital (estos tres filtrados por palabras relacionadas con IA). Probadas el 01/11/2026.

## Límites

- Los feeds fallan de vez en cuando (es normal que falle uno por ronda); el resultado indica cuáles quedaron fuera.
- La agrupación se basa en las palabras del título: a veces agrupa demasiado poco (dos titulares muy distintos sobre el mismo hecho).
- El ángulo solo considera el título y el resumen: los números y hechos siempre se consultan en la fuente abierta.

Licencia: MIT.