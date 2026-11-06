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

## Faixas de zoeira (Santos e Corinthians)

Os dois contadores usam a mesma data, `FIM_BRASILEIRAO` no `index.html` (última rodada, 02/12/2026).
O botão **Arerê** toca `arere.mp3` se esse arquivo existir na raiz do repositório; sem o arquivo,
o navegador canta a frase com a voz do sistema por cima de um batuque gerado na hora.
Para usar um áudio de verdade, basta colocar o `arere.mp3` na raiz e dar push.
Com o arquivo no lugar, o site tenta tocar sozinho ao abrir; como os navegadores bloqueiam som
automático, na prática ele toca no primeiro clique ou toque do visitante em qualquer ponto da página.
Ao abrir o site (uma vez por sessão do navegador) aparece a **tela de entrada "Série B"**: preto e branco
listrado, letreiro piscando, camisa despencando da Série A para a B, contador de dias e confete. Qualquer toque
na tela entra no site; como esse toque é um gesto do visitante, o navegador libera o som, então nesse momento o
Arerê toca (mp3 ou voz) e abre a janela com o player oficial da ESPN (o "syndicated player", feito para ser
embutido) com o clipe da torcida cantando; o visitante dá o play e o som já vem ligado. O vídeo fica nos
servidores da ESPN, o site só embute o player, que não aceita autoplay nem tempo inicial por parâmetro.
Na faixa do Corinthians, **Vídeo** reabre a janela e **Entrada** reabre a tela de entrada.

A faixa do Corinthians ainda tem um letreiro rolante, o número pulsando, uma tremida a cada 7 s e o
"termômetro do rebaixamento", que anda com as 38 rodadas do Brasileirão (`rodada_ao_vivo` ou `ultima_fechada`
do `data.json`) e chega a 100% ("Caiu!") no fim do campeonato. O card do time do corintiano (id 595076)
ganha a faixa diagonal "Série B 2027" e um apelido que troca a cada minuto (lista `ZOEIRA` no `index.html`).

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
