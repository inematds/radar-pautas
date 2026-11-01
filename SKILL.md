---
name: radar-pautas
description: Radar das pautas de IA em alta nas últimas 24 h — lê ~20 fontes públicas (blogs oficiais, imprensa, Hacker News, Reddit, GitHub em alta), junta a mesma notícia vinda de vários sites, dá nota, confere se cada link abre e sugere manchete, gancho e formato (r7ex, explicavideo, carrossel) em português. Gatilho: "o que está em alta", "pautas de hoje", "radar", "o que saiu de IA hoje", "me dá 6 pautas".
---

# radar-pautas

## Rodar
```bash
cd ~/projetos/radar-pautas
python3 radar.py --angulos            # 6 pautas + ângulo em PT (claude -p, assinatura)
python3 radar.py --dry                # só olhar, sem gravar e sem ângulo
python3 radar.py --horas 48 --n 8     # janela maior, mais pautas
```
Saída: `~/projetos/output/radar-pautas/<data>/pautas.md`, `pautas.json`, `radar.html`.

## Como ler o resultado
- **Nota**: (fontes − 1) × 3 + recência × 2 + 1,5 se fonte oficial + 0,8 se cita empresa/produto conhecido, × peso da fonte. Mesma notícia em 3 sites pesa mais que 1 site sozinho.
- **Link (200)**: conferido na hora. Pauta sem link que abre não entra.
- **⚠ Já fizemos**: linha parecida no `~/projetos/wifi/PRODUCOES-VIDEO.md` (mesma empresa + 2 palavras do título). Olhar antes de repetir.
- Variedade: no máximo 2 pautas da mesma empresa e 2 vindas só do mesmo site.

## Depois do radar
- Mostre ao Nei as 6 pautas (manchete PT, por que importa, link) e pergunte quais viram vídeo. **Nada é produzido sem ele escolher.**
- Pauta escolhida → r7ex / explicavideo / carrossel-inema, com o link do radar como fonte de fatos (abrir e ler a fonte antes de escrever qualquer número).

## Regras
- Só páginas públicas (RSS) e GitHub pelo `gh`. Nenhuma chave de API.
- O ângulo é sugestão: o `claude -p` só vê título e resumo; fato e número vêm da fonte aberta.
- Fonte nova: testar o feed (200 e itens) antes de pôr em `fontes.json`.
