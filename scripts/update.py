"""Busca a pontuação dos times na API do Cartola e grava data.json.

Soma só as rodadas RODADA_INICIO..RODADA_FIM. Guarda também a escalação de
cada rodada (a partir de RODADA_INICIO - 1, como aquecimento), o histórico
da temporada (para a chance de título) e se cada time já escalou a próxima
rodada. Durante uma rodada em andamento calcula a parcial ao vivo.
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.cartola.globo.com"
RODADA_INICIO = 29
RODADA_FIM = 38
RODADA_AQUECIMENTO = RODADA_INICIO - 1
CAPITAO_MULT = 1.5

TIMES = [
    2266880,   # ApostaFutebolClube
    595076,    # Alpaca Alvinegra
    26866238,  # Ambafc
]

SAIDA = Path(__file__).resolve().parent.parent / "data.json"

# status_mercado: 1 aberto, 2 fechado (rodada rolando), 4 manutenção, 6 fim de temporada
MERCADO_ABERTO = 1
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


def escalacao(atletas, capitao, pontos_de=None):
    """Lista compacta dos atletas. pontos_de: dict de parciais (rodada ao vivo)."""
    lista = []
    for a in atletas or []:
        if pontos_de is None:
            pts, jogou = a.get("pontos_num"), a.get("entrou_em_campo")
        else:
            p = pontos_de.get(str(a["atleta_id"]))
            pts = p.get("pontuacao") if p else None
            jogou = bool(p) and p.get("entrou_em_campo", True)
        lista.append({
            "id": a["atleta_id"],
            "n": a.get("apelido") or a.get("nome"),
            "pos": a.get("posicao_id"),
            "clube": a.get("clube_id"),
            "pts": None if pts is None else round(float(pts), 2),
            "jogou": bool(jogou),
            "cap": a["atleta_id"] == capitao,
        })
    return lista


def main():
    status = get("/mercado/status")
    rodada_atual = status["rodada_atual"]
    mercado = status["status_mercado"]
    fim_de_jogo = bool(status.get("game_over"))

    ultima_fechada = rodada_atual if fim_de_jogo else rodada_atual - 1
    rodada_ao_vivo = rodada_atual if mercado == MERCADO_FECHADO and not fim_de_jogo else None

    anterior = carregar_anterior()
    ant_times = {t["id"]: t for t in anterior.get("times", [])}
    escalacoes = anterior.get("escalacoes") or {}

    clubes = anterior.get("clubes")
    if not clubes:
        clubes = {cid: {"sigla": c.get("abreviacao"), "nome": c.get("nome_fantasia") or c.get("nome"),
                        "escudo": (c.get("escudos") or {}).get("30x30")}
                  for cid, c in get("/clubes").items()}

    pontuados = {}
    if rodada_ao_vivo and RODADA_AQUECIMENTO <= rodada_ao_vivo <= RODADA_FIM:
        try:
            pontuados = get("/atletas/pontuados").get("atletas") or {}
        except Exception:
            pontuados = {}

    times = []
    for time_id in TIMES:
        info = get(f"/time/id/{time_id}")
        t = info["time"]
        ant = ant_times.get(time_id, {})
        rodadas = dict(ant.get("rodadas") or {})
        historico = dict(ant.get("historico") or {})

        # Rodadas fechadas: pontos oficiais + escalação (cacheadas)
        for r in range(RODADA_AQUECIMENTO, min(ultima_fechada, RODADA_FIM) + 1):
            chave = str(r)
            tem_escalacao = str(time_id) in (escalacoes.get(chave) or {})
            ja_tem_pontos = chave in rodadas or r < RODADA_INICIO
            if tem_escalacao and ja_tem_pontos:
                continue
            dados = get(f"/time/id/{time_id}/{r}")
            pts = round(float(dados.get("pontos") or 0), 2)
            if r >= RODADA_INICIO:
                rodadas[chave] = pts
            else:
                historico[chave] = pts
            escalacoes.setdefault(chave, {})[str(time_id)] = {
                "pontos": pts,
                "atletas": escalacao(dados.get("atletas"), dados.get("capitao_id")),
            }

        # Histórico da temporada antes da disputa (para a chance de título)
        for r in range(1, min(RODADA_AQUECIMENTO, ultima_fechada) + 1):
            if str(r) in historico:
                continue
            try:
                historico[str(r)] = round(float(get(f"/time/id/{time_id}/{r}").get("pontos") or 0), 2)
            except Exception:
                pass

        # Rodada ao vivo: escalação atual + parciais
        parcial = None
        if rodada_ao_vivo and RODADA_AQUECIMENTO <= rodada_ao_vivo <= RODADA_FIM:
            capitao = info.get("capitao_id")
            lista = escalacao(info.get("atletas"), capitao, pontuados)
            if pontuados:
                parcial = round(sum((a["pts"] or 0) * (CAPITAO_MULT if a["cap"] else 1) for a in lista), 2)
            escalacoes.setdefault(str(rodada_ao_vivo), {})[str(time_id)] = {
                "pontos": parcial, "atletas": lista, "ao_vivo": True,
            }

        # Já escalou a próxima rodada? rodada_time_id = última rodada em que salvou o time
        escalou = None
        if mercado == MERCADO_ABERTO and not fim_de_jogo:
            escalou = (t.get("rodada_time_id") or 0) >= rodada_atual

        times.append({
            "id": time_id,
            "nome": t["nome"],
            "cartola": t["nome_cartola"],
            "slug": t["slug"],
            "escudo": t.get("url_escudo_png"),
            "rodadas": dict(sorted(rodadas.items(), key=lambda kv: int(kv[0]))),
            "historico": dict(sorted(historico.items(), key=lambda kv: int(kv[0]))),
            "total": round(sum(rodadas.values()), 2),
            "parcial": parcial,
            "escalou": escalou,
        })

    # Uma rodada que estava ao vivo e fechou: a versão oficial substitui a parcial
    for chave in list(escalacoes):
        r = int(chave)
        if r > RODADA_FIM or r < RODADA_AQUECIMENTO:
            escalacoes.pop(chave)
        elif r != rodada_ao_vivo and r > ultima_fechada:
            escalacoes.pop(chave)

    fechamento = status.get("fechamento") or {}
    dados = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rodada_inicio": RODADA_INICIO,
        "rodada_fim": RODADA_FIM,
        "rodada_aquecimento": RODADA_AQUECIMENTO,
        "rodada_atual": rodada_atual,
        "ultima_fechada": ultima_fechada,
        "rodada_ao_vivo": rodada_ao_vivo,
        "status_mercado": mercado,
        "fim_de_jogo": fim_de_jogo,
        "fechamento": fechamento.get("timestamp"),
        "times": times,
        "escalacoes": dict(sorted(escalacoes.items(), key=lambda kv: int(kv[0]))),
        "clubes": clubes,
    }

    # Sem mudança nos números: mantém o arquivo como está (evita commit à toa)
    velho = dict(anterior)
    velho.pop("atualizado_em", None)
    novo = {k: v for k, v in dados.items() if k != "atualizado_em"}
    if velho == novo:
        print("sem mudanças")
        return
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"ok: rodada {rodada_atual}, mercado {mercado}, fechadas até {ultima_fechada}")
    for t in times:
        print(f"  {t['nome']}: {t['total']} (parcial {t['parcial']}, escalou {t['escalou']}, hist {len(t['historico'])} rodadas)")


if __name__ == "__main__":
    main()
