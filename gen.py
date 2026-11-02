"""
0ph1s // gen.py
Gera os SVGs do perfil no mesmo visual da Axio: fósforo âmbar (P3) sobre vidro
de tubo CRT. Rode `python gen.py` e os arquivos saem em ./assets.
"""

from datetime import date
from html import escape
from pathlib import Path
import json
import subprocess
import textwrap

OUT = Path(__file__).parent / "assets"

# cor (mesmos tokens do style.css da Axio)
GLASS = "#120D08"
GLASS_2 = "#1A130C"
AMBER = "#FFB547"
HOT = "#FFE6B3"
TEXT = "#EBCB98"
DIM = "#A97B4B"
WIRE = "#5A3B1F"
WIRE_2 = "#35230F"
HAZARD = "#FF5A36"

W = 900          # largura de todos os painéis
CW = 0.6         # largura de um caractere monoespaçado, em em

USER = "0ph1s@core"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

STYLE = f"""
text {{ font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, Menlo, 'DejaVu Sans Mono', 'Liberation Mono', monospace; }}
.dim {{ fill: {DIM}; }} .amb {{ fill: {AMBER}; }} .hot {{ fill: {HOT}; }}
.txt {{ fill: {TEXT}; }} .wire {{ fill: {WIRE}; }} .glass {{ fill: {GLASS}; }}
.glow {{ filter: url(#glow); }}
.crt {{ animation: flick 6s steps(1) infinite; }}
.blink {{ animation: blink 1.06s steps(1) infinite; }}
.led {{ animation: led 2.4s steps(1) infinite; }}
.a {{ animation: appear .01s linear both; }}
.on {{ animation: power .5s linear both; }}
.roll {{ animation: roll 8s linear infinite; }}
@keyframes flick {{ 0%,100% {{ opacity: 1 }} 47% {{ opacity: .94 }} 48% {{ opacity: 1 }} 83% {{ opacity: .97 }} }}
@keyframes blink {{ 50% {{ opacity: 0 }} }}
@keyframes led {{ 0%,100% {{ opacity: 1 }} 92% {{ opacity: .25 }} }}
@keyframes appear {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
@keyframes power {{ 0% {{ opacity: 0 }} 10% {{ opacity: 1 }} 18% {{ opacity: .2 }} 30% {{ opacity: 1 }} 38% {{ opacity: .5 }} 50%,100% {{ opacity: 1 }} }}
@keyframes roll {{ from {{ transform: translateY(-120px) }} to {{ transform: translateY(var(--h)) }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
"""


def defs(w, h):
    return f"""<defs>
  <filter id="glow" x="-20%" y="-40%" width="140%" height="180%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">
    <rect y="2" width="4" height="1" fill="#000" opacity=".16"/>
  </pattern>
  <radialGradient id="vig" cx="50%" cy="50%" r="75%">
    <stop offset="60%" stop-color="#000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000" stop-opacity=".55"/>
  </radialGradient>
  <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>
    <stop offset=".5" stop-color="{AMBER}" stop-opacity=".05"/>
    <stop offset="1" stop-color="{AMBER}" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="tube"><rect width="{w}" height="{h}" rx="6"/></clipPath>
</defs>"""


def svg(h, body, label, w=W):
    """Envelope comum: vidro, conteúdo, scanlines, vinheta e a faixa que rola."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">
<style>{STYLE}</style>
{defs(w, h)}
<g clip-path="url(#tube)">
  <rect width="{w}" height="{h}" fill="{GLASS}"/>
  <g class="crt">
{body}
  </g>
  <rect class="roll" style="--h:{h + 120}px" width="{w}" height="120" fill="url(#band)"/>
  <rect width="{w}" height="{h}" fill="url(#scan)"/>
  <rect width="{w}" height="{h}" fill="url(#vig)"/>
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="6" fill="none" stroke="{WIRE}"/>
</svg>
"""


def t(x, y, s, cls="txt", size=13, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" {extra}>{s}</text>'


def e(s):
    return escape(s, quote=False)


def delay(sec):
    return f'style="animation-delay:{sec}s"'


def prompt(x, y, cmd, size=14):
    return t(x, y, f'<tspan class="amb">{USER}</tspan><tspan class="dim">:~$ </tspan><tspan class="txt">{e(cmd)}</tspan>', "txt", size)


def typed(x, y, cmd, begin, size=14, cid="type"):
    """Prompt cujo comando é digitado caractere a caractere (SMIL discreto)."""
    pre = len(USER) + 4
    cw = CW * size
    x0 = x + pre * cw
    n = len(cmd)
    vals = ";".join(f"{(i + 1) * cw:.1f}" for i in range(n)) + f";{n * cw + 40:.1f}"
    dur = 0.055 * (n + 1)
    return f"""<clipPath id="{cid}"><rect x="{x0}" y="{y - size}" width="0" height="{size + 6}">
  <animate attributeName="width" values="{vals}" dur="{dur:.2f}s" begin="{begin}s" calcMode="discrete" fill="freeze"/>
</rect></clipPath>
{t(x, y, f'<tspan class="amb">{USER}</tspan><tspan class="dim">:~$ </tspan>', "txt", size)}
<g clip-path="url(#{cid})">{t(x0, y, e(cmd), "txt", size)}</g>"""


def caret(x, y, size=14, extra=""):
    return f'<rect class="blink" x="{x}" y="{y - size + 2}" width="{CW * size:.1f}" height="{size + 1}" fill="{AMBER}" {extra}/>'


def bar(x, y, w, left, right, active=True):
    fill = "rgba(255,181,71,.07)" if active else GLASS_2
    cls = "amb" if active else "dim"
    return f"""<rect x="{x}" y="{y}" width="{w}" height="26" fill="{fill}"/>
<line x1="{x}" y1="{y + 26.5}" x2="{x + w}" y2="{y + 26.5}" stroke="{WIRE_2}"/>
{t(x + 14, y + 17, e(left), cls, 12)}
{t(x + w - 14, y + 17, e(right), cls, 12, 'text-anchor="end"')}"""


# ---------------------------------------------------------------------------
# Logo ANSI Shadow desenhado como vetor (não depende da fonte do leitor)
# ---------------------------------------------------------------------------

GLYPHS = {
    "0": [" ██████╗ ", "██╔═████╗", "██║██╔██║", "████╔╝██║", "╚██████╔╝", " ╚═════╝ "],
    "P": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "1": [" ██╗", "███║", "╚██║", " ██║", " ██║", " ╚═╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
}


def ansi_logo(word, x, y, cw, ch):
    rows = ["".join(GLYPHS[c][r] for c in word) for r in range(6)]
    blocks, lines = [], []
    d = cw * 0.17
    for r, row in enumerate(rows):
        y0, y1 = y + r * ch, y + (r + 1) * ch
        cy = (y0 + y1) / 2
        c = 0
        while c < len(row):
            if row[c] == "█":
                start = c
                while c < len(row) and row[c] == "█":
                    c += 1
                blocks.append(f"M{x + start * cw:.1f} {y0:.1f}h{(c - start) * cw:.1f}v{ch:.1f}h{-(c - start) * cw:.1f}z")
                continue
            x0, x1 = x + c * cw, x + (c + 1) * cw
            cx = (x0 + x1) / 2
            g = row[c]
            if g == "═":
                lines.append(f"M{x0:.1f} {cy - d:.1f}H{x1:.1f}M{x0:.1f} {cy + d:.1f}H{x1:.1f}")
            elif g == "║":
                lines.append(f"M{cx - d:.1f} {y0:.1f}V{y1:.1f}M{cx + d:.1f} {y0:.1f}V{y1:.1f}")
            elif g == "╗":
                lines.append(f"M{x0:.1f} {cy - d:.1f}H{cx + d:.1f}V{y1:.1f}M{x0:.1f} {cy + d:.1f}H{cx - d:.1f}V{y1:.1f}")
            elif g == "╔":
                lines.append(f"M{x1:.1f} {cy - d:.1f}H{cx - d:.1f}V{y1:.1f}M{x1:.1f} {cy + d:.1f}H{cx + d:.1f}V{y1:.1f}")
            elif g == "╚":
                lines.append(f"M{cx - d:.1f} {y0:.1f}V{cy + d:.1f}H{x1:.1f}M{cx + d:.1f} {y0:.1f}V{cy - d:.1f}H{x1:.1f}")
            elif g == "╝":
                lines.append(f"M{cx + d:.1f} {y0:.1f}V{cy + d:.1f}H{x0:.1f}M{cx - d:.1f} {y0:.1f}V{cy - d:.1f}H{x0:.1f}")
            c += 1
    return (f'<path d="{"".join(lines)}" fill="none" stroke="{AMBER}" stroke-opacity=".6" stroke-width="1.3"/>'
            f'<path d="{"".join(blocks)}" fill="{AMBER}"/>'), len(rows[0]) * cw


# ---------------------------------------------------------------------------
# Painéis
# ---------------------------------------------------------------------------

def header():
    h = 440
    p = []
    p.append(bar(0, 0, W, "0ph1s@core: ~  —  tty1", "online", active=False))
    p.append(f'<rect class="led" x="{W - 76}" y="10" width="7" height="7" fill="{AMBER}" filter="url(#glow)"/>')

    boot = [
        ("montando /dev/dados", "ok"),
        ("carregando modelos ........ python · keras · scikit-learn", "ok"),
        ("compilando interface ...... react · webgl · gsap", "ok"),
        ("iniciando simulador ....... haskell", "ok"),
    ]
    for i, (msg, st) in enumerate(boot):
        y = 58 + i * 19
        p.append(t(36, y, f'<tspan class="dim">[ </tspan><tspan class="hot">{st}</tspan><tspan class="dim"> ]</tspan> {e(msg)}',
                   "txt a", 12, delay(0.25 + i * 0.3)))

    p.append(typed(36, 150, "./peterson --init", 1.6))

    logo, lw = ansi_logo("0PH1S", 36, 174, 12, 22)
    p.append(f'<g class="on glow" {delay(2.8)}>{logo}</g>')

    # bloco estilo neofetch ao lado do logo
    ix, vx = 540, 622
    info = [
        ("nome", "Peterson Carara"),
        ("curso", "Ciência de Dados"),
        ("campus", "FATEC Baixada Santista"),
        ("local", "Brasil"),
        ("shell", "python · js · haskell"),
        ("foco", "dados · web · baixo nível"),
    ]
    g = [t(ix, 186, '<tspan class="amb">peterson</tspan><tspan class="dim">@</tspan><tspan class="amb">0ph1s</tspan>', "txt", 14),
         f'<line x1="{ix}" y1="196" x2="{ix + 250}" y2="196" stroke="{WIRE}" stroke-dasharray="3 3"/>']
    for i, (k, v) in enumerate(info):
        y = 218 + i * 19
        g.append(t(ix, y, e(k), "dim", 13))
        g.append(t(vx, y, e(v), "hot" if k == "nome" else "txt", 13))
    ramp = [GLASS_2, WIRE_2, WIRE, DIM, TEXT, AMBER, HOT, HAZARD]
    for i, c in enumerate(ramp):
        g.append(f'<rect x="{ix + i * 26}" y="{218 + 6 * 19 - 4}" width="22" height="12" fill="{c}"/>')
    p.append(f'<g class="a" {delay(3.2)}>{"".join(g)}</g>')

    p.append(t(36, 372, "Transformo dados em decisões e ideias em interfaces.", "hot glow a", 21, delay(3.6)))

    p.append(f'<g class="a" {delay(4.0)}>{prompt(36, 412, "")}{caret(36 + (len(USER) + 4) * CW * 14, 412)}</g>')
    return svg(h, "\n".join(p), "0PH1S — Peterson Carara, estudante de Ciência de Dados na FATEC Baixada Santista. "
                                 "Transformo dados em decisões e ideias em interfaces.")


def strip(cmd, right=""):
    """Faixa de seção: um prompt, como os títulos da Axio."""
    h = 46
    p = [prompt(24, 29, cmd), caret(24 + (len(USER) + 4 + len(cmd) + 1) * CW * 14, 29)]
    if right:
        p.append(t(W - 24, 29, e(right), "dim", 12, 'text-anchor="end"'))
    return svg(h, "\n".join(p), f"{USER}:~$ {cmd}")


def flags(x, y, items, kw=150):
    out = []
    for i, (k, v) in enumerate(items):
        yy = y + i * 24
        out.append(f'<line x1="{x}" y1="{yy - 16}" x2="{x + 380}" y2="{yy - 16}" stroke="{WIRE_2}" stroke-dasharray="3 3"/>')
        out.append(t(x, yy, e(k), "amb", 12.5))
        out.append(t(x + kw, yy, e(v), "dim", 12.5))
    return "\n".join(out)


def art(x, y, lines, size=13, lh=15.5):
    return "\n".join(t(x, y + i * lh, e(l), "amb", size, 'xml:space="preserve"') for i, l in enumerate(lines))


def stack():
    h = 380
    mw = 470                       # painel principal
    sx = mw                        # painéis laterais
    sw = W - mw
    sh = (h - 28) / 2
    p = []

    # pane 0: data science
    p.append(bar(0, 0, mw, "~/stack/data-science", "model: ready"))
    p.append(f'<rect x="0.5" y="0.5" width="{mw - 1}" height="{h - 29}" fill="none" stroke="{AMBER}" stroke-opacity=".9"/>')
    chart = [
        "  ▲",
        "  │                · ╭──",
        "  │          ·  ·╭──╯·",
        "  │       ·  ╭──╯  ·",
        "  │    · ╭──╯·",
        "  │  ·╭──╯  ·",
        "  │╭──╯·",
        "  └─────────────────────▶",
    ]
    p.append(f'<g class="glow">{art(26, 58, chart)}</g>')
    p.append(t(240, 92, "Data Science", "hot glow", 26))
    p.append(t(240, 116, "modelos que encontram", "txt", 12.5))
    p.append(t(240, 134, "padrões e antecipam", "txt", 12.5))
    p.append(t(240, 152, "o que vem a seguir.", "txt", 12.5))
    p.append(flags(26, 222, [
        ("--machine-learning", "redes neurais, KerasTuner"),
        ("--estatistica", "Kruskal-Wallis, Mann-Whitney"),
        ("--reducao-dim", "PCA e atributos"),
        ("--analise", "pandas, scikit-learn, R"),
        ("--notebooks", "Jupyter, visualização"),
    ], kw=170))

    # pane 1: web
    p.append(f'<line x1="{sx + .5}" y1="0" x2="{sx + .5}" y2="{h - 28}" stroke="{WIRE}"/>')
    p.append(bar(sx, 0, sw, "~/stack/web", "build: passing", active=False))
    p.append(t(sx + 26, 62, "Web", "hot", 22))
    p.append(t(sx + 92, 62, "rápida, imersiva e acessível", "dim", 12))
    p.append(flags(sx + 26, 96, [
        ("--react", "vite · tailwind"),
        ("--imersivo", "webgl · shaders · gsap"),
        ("--backend", "django · mysql"),
    ], kw=120))

    # pane 2: pesquisa
    p.append(f'<line x1="{sx}" y1="{sh + .5}" x2="{W}" y2="{sh + .5}" stroke="{WIRE}"/>')
    p.append(bar(sx, sh, sw, "~/stack/pesquisa", "sim: running", active=False))
    p.append(t(sx + 26, sh + 62, "Pesquisa", "hot", 22))
    p.append(t(sx + 152, sh + 62, "o que há abaixo da abstração", "dim", 12))
    p.append(flags(sx + 26, sh + 96, [
        ("--haskell", "FSM de aviônica de UAV"),
        ("--ic", "iniciação científica, FATEC"),
        ("--latex", "artigos e relatórios"),
    ], kw=120))

    # barra de status do tmux
    p.append(f'<rect x="0" y="{h - 28}" width="{W}" height="28" fill="{AMBER}"/>')
    p.append(t(12, h - 9, '<tspan font-weight="700">[0ph1s]</tspan>   '
                          '<tspan font-weight="700">0:data-science*</tspan>   1:web   2:pesquisa', "glass", 12.5))
    p.append(t(W - 12, h - 9, "ciência de dados · 2026", "glass", 12.5, 'text-anchor="end"'))
    return svg(h, "\n".join(p), "Stack: Data Science (machine learning, estatística, PCA, pandas, scikit-learn), "
                                "Web (React, WebGL, GSAP, Django) e Pesquisa (Haskell, iniciação científica, LaTeX).")


SIGNALS = ["▁▂▃▅▇▅▃▂▁▂▃▅", "▂▄▆█▆▄▂▄▆█▆▄", "▇▅▃▁▃▅▇▅▃▁▃▅", "▁▃▆▃▁▃▆▃▁▃▆▃", "▅▅▇▇▃▃▅▅▇▇▃▃", "▁▁▂▃▅█▅▃▂▁▁▂"]


def card(i, repo, title, desc, stack, tag):
    w, h = 440, 196
    p = []
    p.append(f'<rect x="0" y="0" width="{w}" height="30" fill="{GLASS_2}"/>')
    p.append(f'<line x1="0" y1="30.5" x2="{w}" y2="30.5" stroke="{WIRE_2}"/>')
    p.append(t(16, 20, f"CH{i}", "amb glow", 13, 'font-weight="700"'))
    p.append(t(58, 20, e(tag), "dim", 12))
    p.append(f'<rect class="blink" x="{w - 62}" y="14" width="7" height="7" fill="{HAZARD}"/>')
    p.append(t(w - 16, 21, "live", "dim", 12, 'text-anchor="end"'))

    p.append(t(16, 60, e(title), "hot glow", 17))
    for j, line in enumerate(textwrap.wrap(desc, 56)[:3]):
        p.append(t(16, 84 + j * 17, e(line), "txt", 12))
    p.append(f'<line x1="16" y1="138" x2="{w - 16}" y2="138" stroke="{WIRE}" stroke-dasharray="3 3"/>')
    p.append(t(16, 158, '<tspan class="dim">stack </tspan>' + e(stack), "amb", 12))
    p.append(t(w - 16, 158, SIGNALS[(i - 1) % len(SIGNALS)], "amb", 12, 'text-anchor="end" opacity=".7"'))
    p.append(t(16, 182, "&gt; OPEN_REPO ↗", "amb", 12, 'font-weight="700"'))
    p.append(t(w - 16, 182, e(f"0ph1s/{repo}"[:44]), "dim", 11, 'text-anchor="end"'))

    return svg(h, "\n".join(p), f"{title}: {desc}", w)


PROJECTS = [
    ("soccerplayers-v2", "Academias de formação no futebol",
     "35 jogadores de quatro academias comparados por percentil na posição, com Kruskal-Wallis e Mann-Whitney.",
     "python · react · vite", "data analytics / web"),
    ("django_movie_recommendation", "Ângulo: recomendação de filmes",
     "TF-IDF, similaridade do cosseno e filtro híbrido. O perfil do usuário muda a cada curtida, sem treino.",
     "django · scikit-learn · webgl", "data science / web"),
    ("Neural-Network-Approach-to-Binary-Logistic-Classification-of-Potentially-Hazardous-Asteroids",
     "Asteroides potencialmente perigosos",
     "Rede neural densa ajustada com KerasTuner sobre dados da NASA. Acurácia de 91% e AUC de 0.91.",
     "python · keras", "data science"),
    ("Principal-Component-Analysis-of-the-Solar-System-Planets", "PCA dos planetas do Sistema Solar",
     "Atributos dos oito planetas reduzidos aos componentes principais, revelando rochosos e gigantes em 3D.",
     "python · pandas · scikit-learn", "data analytics"),
    ("avionics-crem", "Aviônica de UAV em Haskell",
     "Máquina de estados de aviônica com CREM e um simulador puro. Iniciação científica na FATEC.",
     "haskell", "pesquisa / ic"),
    ("axio", "Axio",
     "Landing page com shader ASCII em WebGL, efeitos CRT e animações com GSAP. De onde vem este visual.",
     "javascript · webgl · gsap", "web / imersivo"),
]


QUERY = """query($login: String!) { user(login: $login) {
  createdAt followers { totalCount }
  repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
    totalCount nodes { stargazerCount languages(first: 10) { edges { size node { name } } } }
  }
  contributionsCollection { contributionCalendar {
    totalContributions weeks { contributionDays { contributionCount } }
  } }
} }"""


def github_data(login="0ph1s"):
    """Lê os números públicos do perfil pela gh CLI (precisa de `gh auth login`)."""
    raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={login}"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    u = json.loads(raw)["data"]["user"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] = langs.get(edge["node"]["name"], 0) + edge["size"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "since": u["createdAt"][:4],
        "contrib": cal["totalContributions"],
        "weeks": [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]],
        "langs": sorted(langs.items(), key=lambda kv: -kv[1]),
    }


def diag(d):
    h = 372
    p = [bar(0, 0, W, "~/diagnostico", f"snapshot {date.today():%d.%m.%Y}")]

    # coluna esquerda: leitura do sistema
    rows = [
        ("REPOS", f"{d['repos']} públicos"),
        ("STARS", str(d["stars"])),
        ("FOLLOWERS", str(d["followers"])),
        ("CONTRIB 12M", str(d["contrib"])),
        ("UPTIME", f"desde {d['since']}"),
        ("SYSTEM", "ONLINE"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 60 + i * 24
        p.append(t(26, y, k, "dim", 12.5))
        p.append(t(300, y, e(v), "hot", 12.5, 'text-anchor="end"'))
        p.append(f'<line x1="26" y1="{y + 8}" x2="300" y2="{y + 8}" stroke="{WIRE_2}" stroke-dasharray="1 3"/>')
    p.append(f'<rect class="led" x="{300 - 6 * CW * 12.5 - 16:.1f}" y="{60 + 5 * 24 - 8}" width="7" height="7" fill="{AMBER}" filter="url(#glow)"/>')

    # coluna direita: linguagens como barras de caracteres
    top = d["langs"][:6]
    total = sum(v for _, v in d["langs"]) or 1
    cells = 24
    p.append(t(350, 42 + 18, "linguagens", "amb", 12.5))
    for i, (name, size) in enumerate(top):
        y = 60 + (i + 1) * 22
        pct = size / total
        full = round(pct * cells)
        p.append(t(350, y, e(name.lower().replace(" notebook", "")[:14]), "txt", 12.5))
        # cada célula é um "█" desenhado como retângulo, para não depender da fonte
        for c in range(cells):
            on = c < full
            p.append(f'<rect x="{480 + c * 13}" y="{y - 11}" width="11" height="13" fill="{AMBER if on else WIRE_2}"'
                     f'{" filter=\"url(#glow)\"" if on else ""}/>')
        p.append(t(W - 26, y, f"{pct * 100:4.1f}%", "dim", 12.5, 'text-anchor="end"'))

    # mapa de contribuições: as últimas 53 semanas em quatro níveis de fósforo
    y0 = 222
    p.append(t(26, y0 - 10, "atividade · últimas 53 semanas", "amb", 12.5))
    weeks = d["weeks"][-53:]
    peak = max((c for w in weeks for c in w), default=0) or 1
    ramp = [WIRE_2, WIRE, DIM, AMBER, HOT]
    step = (W - 52) / 53
    size = step - 3
    for wi, week in enumerate(weeks):
        for di, c in enumerate(week):
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            x = 26 + wi * step
            y = y0 + di * (size + 3)
            p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" fill="{ramp[lvl]}"/>')
    ly = y0 + 7 * (size + 3) + 14
    p.append(t(26, ly, "menos", "dim", 11))
    for i, c in enumerate(ramp):
        p.append(f'<rect x="{70 + i * 16}" y="{ly - 9}" width="11" height="11" fill="{c}"/>')
    p.append(t(70 + 5 * 16 + 4, ly, "mais", "dim", 11))
    return svg(h, "\n".join(p), f"Diagnóstico: {d['repos']} repositórios públicos, {d['stars']} estrelas, "
                                f"{d['followers']} seguidores, {d['contrib']} contribuições em 12 meses. "
                                f"Linguagens: {', '.join(n for n, _ in top)}.")


def footer():
    h = 132
    p = [
        prompt(24, 34, "exit"),
        t(24, 58, "logout", "dim", 13),
        t(24, 80, "Connection to 0ph1s closed. Obrigado pela visita.", "txt", 13),
        prompt(24, 112, ""),
        caret(24 + (len(USER) + 4) * CW * 14, 112),
        t(W - 24, 112, "~ fim da transmissão ~", "dim", 12, 'text-anchor="end"'),
    ]
    return svg(h, "\n".join(p), "exit. Obrigado pela visita.")


def main():
    OUT.mkdir(exist_ok=True)
    files = {
        "header.svg": header(),
        "stack.svg": stack(),
        "footer.svg": footer(),
        "cmd-stack.svg": strip("tmux attach -t stack", "3 painéis"),
        "cmd-projetos.svg": strip("git log --author=0ph1s", "6 canais"),
        "cmd-diag.svg": strip("./diagnostico --github", "gh api graphql"),
        "diag.svg": diag(github_data()),
    }
    for i, prj in enumerate(PROJECTS, 1):
        files[f"ch{i}.svg"] = card(i, *prj)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print("ok", name)


if __name__ == "__main__":
    main()
