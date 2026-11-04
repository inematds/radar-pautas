# radar-pautas

[![radar-pautas — as 6 pautas de IA do dia](guia/assets/banner.jpg)](https://inematds.github.io/radar-pautas/guia/)

**🇧🇷 Português · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O radar-pautas é um script que lê, de uma vez, cerca de 20 sites de notícias de inteligência artificial (blogs das empresas, imprensa, Hacker News, Reddit e os projetos que mais ganharam estrelas no GitHub na semana) e devolve as 6 pautas mais quentes das últimas 24 horas. Serve para quem produz conteúdo e precisa decidir rápido o assunto do dia. Ele junta a mesma notícia vinda de vários sites, dá uma nota, confere se o link abre, avisa se você já fez algo parecido e, se pedir, sugere manchete, gancho e formato em português. Precisa de Python 3; o GitHub CLI (`gh`) e o Claude Code são opcionais.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/radar-pautas/guia/**

## Usar

```bash
git clone https://github.com/inematds/radar-pautas ~/projetos/radar-pautas
cd ~/projetos/radar-pautas
python3 radar.py --dry          # olhar as 6 pautas sem gravar
python3 radar.py --angulos      # gravar + manchete/gancho/formato em PT (Claude Code)
```

Abra `~/projetos/output/radar-pautas/<data>/radar.html` no navegador.

| Opção | Faz |
|---|---|
| `--horas 48` | janela de tempo (padrão 24) |
| `--n 8` | quantas pautas (padrão 6) |
| `--angulos` | manchete, por que importa, gancho, formato e palavra, pelo `claude -p` (assinatura) |
| `--sem-github` | sem os repositórios em alta |
| `--dry` | só imprime |

## O processo, do início ao fim

🧠 sessão com o Nei · ⚙️ script/timer · 🤖 `claude -p` (assinatura)

| # | Passo | Comando / o que acontece | Quem |
|---|---|---|---|
| 1 | Coleta | `radar.py` lê os feeds de `fontes.json` em paralelo (e tenta de novo quando o site pede para esperar) + `gh search repos` | ⚙️ |
| 2 | Junta e dá nota | mesma notícia em vários sites vira um assunto; nota por fontes, recência, fonte oficial | ⚙️ |
| 3 | Confere | abre o link de cada pauta (só entra com 200) e procura parecido no `PRODUCOES-VIDEO.md` | ⚙️ |
| 4 | Ângulo | `--angulos`: manchete PT, gancho, formato (r7ex/explicavideo/carrossel) e palavra | 🤖 |
| 5 | Escolha | o Nei escolhe quais pautas viram vídeo ou carrossel | 🧠 |
| 6 | Diário (opcional) | `systemd/radar-pautas.timer` às 07:30 — **vem desligado**; ligar só com OK | ⚙️ |

## Fontes

`fontes.json`: OpenAI, Google AI, Google DeepMind, Hugging Face, NVIDIA, Mistral, GitHub Blog, The Verge, TechCrunch, Ars Technica, Wired, The Decoder, MarkTechPost, MIT News, Simon Willison, Hacker News (150+ pontos), r/LocalLLaMA, Tecmundo, Canaltech e Olhar Digital (esses três filtrados por palavras de IA). Testadas em 01/11/2026.

## Limites

- Feeds caem de vez em quando (um por rodada é normal); o resultado diz quais ficaram fora.
- O agrupamento é por palavras do título: às vezes junta de menos (duas manchetes muito diferentes do mesmo fato).
- O ângulo vê só título e resumo: número e fato, sempre da fonte aberta.

Licença: MIT.
