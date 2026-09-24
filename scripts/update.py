"""Busca a pontuação dos times na API do Cartola e grava data.json.

Soma só as rodadas RODADA_INICIO..RODADA_FIM. Durante uma rodada em
andamento (mercado fechado), calcula a parcial ao vivo do time.
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.cartola.globo.com"
RODADA_INICIO = 29
RODADA_FIM = 38
CAPITAO_MULT = 1.5

TIMES = [
    2266880,   # ApostaFutebolClube
    595076,    # Alpaca Alvinegra
    26866238,  # Ambafc
]

SAIDA = Path(__file__).resolve().parent.parent / "data.json"

# status_mercado: 1 aberto, 2 fechado (rodada rolando), 4 manutenção, 6 fim de temporada
MERCADO_FECHADO = 2


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "camp-cartola/1.0"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception:
            if tentativa == 2:
                raise
            time.sleep(3)


def carregar_anterior():
    try:
        return json.loads(SAIDA.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    status = get("/mercado/status")
    rodada_atual = status["rodada_atual"]
    mercado = status["status_mercado"]
    fim_de_jogo = bool(status.get("game_over"))

    # Última rodada fechada (com pontuação oficial)
    if fim_de_jogo:
        ultima_fechada = rodada_atual
    else:
        ultima_fechada = rodada_atual - 1
    rodada_ao_vivo = rodada_atual if mercado == MERCADO_FECHADO and not fim_de_jogo else None

    # Reaproveita rodadas já fechadas do data.json anterior para economizar chamadas
    anterior = {t["id"]: t for t in carregar_anterior().get("times", [])}

    pontuados = {}
    if rodada_ao_vivo and RODADA_INICIO <= rodada_ao_vivo <= RODADA_FIM:
        try:
            pontuados = get("/atletas/pontuados").get("atletas") or {}
        except Exception:
            pontuados = {}

    times = []
    for time_id in TIMES:
        info = get(f"/time/id/{time_id}")
        t = info["time"]
        rodadas = {k: v for k, v in (anterior.get(time_id, {}).get("rodadas") or {}).items()}

        for r in range(RODADA_INICIO, min(ultima_fechada, RODADA_FIM) + 1):
            if str(r) in rodadas:
                continue
            dados = get(f"/time/id/{time_id}/{r}")
            rodadas[str(r)] = round(float(dados.get("pontos") or 0), 2)

        parcial = None
        if rodada_ao_vivo and pontuados:
            capitao = info.get("capitao_id")
            soma = 0.0
            for a in info.get("atletas") or []:
                p = pontuados.get(str(a["atleta_id"]))
                if not p:
                    continue
                pts = float(p.get("pontuacao") or 0)
                soma += pts * CAPITAO_MULT if a["atleta_id"] == capitao else pts
            parcial = round(soma, 2)

        times.append({
            "id": time_id,
            "nome": t["nome"],
            "cartola": t["nome_cartola"],
            "slug": t["slug"],
            "escudo": t.get("url_escudo_png"),
            "rodadas": dict(sorted(rodadas.items(), key=lambda kv: int(kv[0]))),
            "total": round(sum(rodadas.values()), 2),
            "parcial": parcial,
        })

    fechamento = status.get("fechamento") or {}
    dados = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rodada_inicio": RODADA_INICIO,
        "rodada_fim": RODADA_FIM,
        "rodada_atual": rodada_atual,
        "ultima_fechada": ultima_fechada,
        "rodada_ao_vivo": rodada_ao_vivo,
        "status_mercado": mercado,
        "fim_de_jogo": fim_de_jogo,
        "fechamento": fechamento.get("timestamp"),
        "times": times,
    }
    # Sem mudança nos números: mantém o arquivo como está (evita commit à toa)
    velho = carregar_anterior()
    velho.pop("atualizado_em", None)
    novo = {k: v for k, v in dados.items() if k != "atualizado_em"}
    if velho == novo:
        print("sem mudanças")
        return
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok: rodada {rodada_atual}, mercado {mercado}, fechadas até {ultima_fechada}")
    for t in times:
        print(f"  {t['nome']}: {t['total']} (parcial {t['parcial']})")


if __name__ == "__main__":
    main()
