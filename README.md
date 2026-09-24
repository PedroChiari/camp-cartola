# Camp da Camisa

Disputa de Cartola FC entre **ApostaFutebolClube**, **Alpaca Alvinegra** e **Ambafc**.
Contam só as rodadas **29 a 38** do Brasileirão 2026. Quem somar mais leva a camisa.

## Como funciona

- `scripts/update.py` busca os pontos na API pública do Cartola e grava `data.json`.
- `.github/workflows/atualizar.yml` roda o script a cada 20 minutos e faz commit do `data.json` quando algo muda.
- `index.html` é o site: lê o `data.json` e mostra líder, diferença dos outros, gráfico e tabela.

Com a rodada rolando (mercado fechado), o site mostra a **parcial ao vivo**, estimada com
os titulares e o capitão valendo 1,5x. O valor oficial entra quando a rodada termina.

## Publicar no GitHub Pages

1. Crie um repositório público em https://github.com/new (ex.: `camp-cartola`), sem README.
2. Nesta pasta:
   ```
   git add .
   git commit -m "Camp da Camisa"
   git branch -M main
   git remote add origin https://github.com/PedroChiari/camp-cartola.git
   git push -u origin main
   ```
3. No repositório: **Settings → Pages → Source: Deploy from a branch → main / (root) → Save**.
4. **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**.
5. Aba **Actions → Atualizar pontuação → Run workflow** para testar.

O site fica em `https://PedroChiari.github.io/camp-cartola/`.

## Mudar times ou rodadas

Edite `TIMES`, `RODADA_INICIO` e `RODADA_FIM` no topo de `scripts/update.py`. O ID de um time sai de
`https://api.cartola.globo.com/times?q=NOME` (campo `time_id`). Se trocar um time, ajuste também a cor
dele em `CORES` no `index.html`.

## Rodar local

```
python scripts/update.py
python -m http.server 8000
```
Abra http://localhost:8000.
