"""
0ph1s // gen.py
Gera os SVGs do perfil em estilo terminal/ASCII. Cada painel sai duas vezes,
com as cores do tema claro e do escuro do GitHub, em ./assets/light e
./assets/dark; o README escolhe entre eles com <picture>. O tema "axio" (âmbar
sobre vidro de CRT) continua aqui para quem quiser voltar a ele:
`python gen.py axio`.
"""

from datetime import date
from html import escape
from pathlib import Path
import json
import subprocess
import sys
import textwrap

OUT = Path(__file__).parent / "assets"

# Os nomes vêm do style.css da Axio e valem para todos os temas:
# GLASS fundo, GLASS_2 superfícies, AMBER destaque, HOT ênfase, TEXT texto,
# DIM secundário, WIRE bordas, WIRE_2 divisórias, HAZARD erro.
MONO_GH = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    # Primer, tema escuro padrão do GitHub
    "dark": dict(
        GLASS="#0d1117", GLASS_2="#151b23", AMBER="#4493f8", HOT="#f0f6fc", TEXT="#d1d9e0",
        DIM="#9198a1", WIRE="#3d444d", WIRE_2="#262c36", HAZARD="#f85149",
        USR="#3fb950", LIVE="#3fb950", LOGO="#f0f6fc", LOGO_SHADOW="#9198a1",
        ORANGE="#f0883e", ACTIVE="rgba(68,147,248,.08)", STATUS_BG="#151b23", STATUS_FG="#9198a1",
        HEAT=["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
        SWATCH=["#196c2e", "#2ea043", "#56d364", "#4493f8", "#ab7df8", "#db61a2", "#d29922", "#f85149"],
        FONT=MONO_GH, CRT=False, INVERT=False,
    ),
    # Primer, tema claro padrão do GitHub
    "light": dict(
        GLASS="#ffffff", GLASS_2="#f6f8fa", AMBER="#0969da", HOT="#1f2328", TEXT="#1f2328",
        DIM="#59636e", WIRE="#d1d9e0", WIRE_2="#e6eaef", HAZARD="#d1242f",
        USR="#1a7f37", LIVE="#1a7f37", LOGO="#1f2328", LOGO_SHADOW="#818b98",
        ORANGE="#bc4c00", ACTIVE="rgba(9,105,218,.06)", STATUS_BG="#f6f8fa", STATUS_FG="#59636e",
        HEAT=["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
        SWATCH=["#4ac26b", "#2da44e", "#116329", "#0969da", "#8250df", "#bf3989", "#9a6700", "#d1242f"],
        FONT=MONO_GH, CRT=False, INVERT=True,
    ),
    # fósforo âmbar (P3) sobre vidro de tubo CRT, como na Axio
    "axio": dict(
        GLASS="#120D08", GLASS_2="#1A130C", AMBER="#FFB547", HOT="#FFE6B3", TEXT="#EBCB98",
        DIM="#A97B4B", WIRE="#5A3B1F", WIRE_2="#35230F", HAZARD="#FF5A36",
        USR="#FFB547", LIVE="#FF5A36", LOGO="#FFB547", LOGO_SHADOW="#FFB547",
        ORANGE="#FF8A3D", ACTIVE="rgba(255,181,71,.07)", STATUS_BG="#FFB547", STATUS_FG="#120D08",
        HEAT=["#35230F", "#5A3B1F", "#A97B4B", "#FFB547", "#FFE6B3"],
        SWATCH=["#1A130C", "#35230F", "#5A3B1F", "#A97B4B", "#EBCB98", "#FFB547", "#FFE6B3", "#FF5A36"],
        FONT="'IBM Plex Mono', 'SFMono-Regular', Consolas, Menlo, 'DejaVu Sans Mono', 'Liberation Mono', monospace",
        CRT=True, INVERT=False,
    ),
}


def use(theme):
    """Troca a paleta ativa: as funções abaixo leem estes globais."""
    globals().update(THEMES[theme])


use("dark")

W = 900          # largura de todos os painéis
CW = 0.6         # largura de um caractere monoespaçado, em em

USER = "0ph1s@core"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

def style():
    return f"""
text {{ font-family: {FONT}; }}
.dim {{ fill: {DIM}; }} .amb {{ fill: {AMBER}; }} .hot {{ fill: {HOT}; }} .usr {{ fill: {USR}; }}
.txt {{ fill: {TEXT}; }} .wire {{ fill: {WIRE}; }} .glass {{ fill: {GLASS}; }} .status {{ fill: {STATUS_FG}; }} .ora {{ fill: {ORANGE}; }}
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
    # sem CRT o "brilho" vira um filtro neutro: o GitHub é plano
    blur = '<feGaussianBlur stdDeviation="2.2" result="b"/>' if CRT else ""
    merge = '<feMergeNode in="b"/>' if CRT else ""
    return f"""<defs>
  <filter id="glow" x="-20%" y="-40%" width="140%" height="180%">
    {blur}
    <feMerge>{merge}<feMergeNode in="SourceGraphic"/></feMerge>
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
    """Envelope comum. Nos temas do GitHub o fundo é transparente e não há moldura:
    o conteúdo fica direto sobre a página. No tema axio ganha vidro, borda,
    scanlines, vinheta e a faixa que rola, com uma margem interna."""
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{{W_}}" height="{{H_}}" viewBox="0 0 {{W_}} {{H_}}" role="img" aria-label="{escape(label)}">
<style>{style()}</style>
'''
    if not CRT:
        return head.replace("{W_}", str(w)).replace("{H_}", str(h)) + f"""{defs(w, h)}
{body}
</svg>
"""
    px, py = 24, 20
    w2, h2 = w + 2 * px, h + 2 * py
    return head.replace("{W_}", str(w2)).replace("{H_}", str(h2)) + f"""{defs(w2, h2)}
<g clip-path="url(#tube)">
  <rect width="{w2}" height="{h2}" fill="{GLASS}"/>
  <g class="crt" transform="translate({px} {py})">
{body}
  </g>
  <rect class="roll" style="--h:{h2 + 120}px" width="{w2}" height="120" fill="url(#band)"/>
  <rect width="{w2}" height="{h2}" fill="url(#scan)"/>
  <rect width="{w2}" height="{h2}" fill="url(#vig)"/>
</g>
<rect x=".5" y=".5" width="{w2 - 1}" height="{h2 - 1}" rx="6" fill="none" stroke="{WIRE}"/>
</svg>
"""


def t(x, y, s, cls="txt", size=13, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" {extra}>{s}</text>'


def e(s):
    return escape(s, quote=False)


def delay(sec):
    return f'style="animation-delay:{sec}s"'


def prompt(x, y, cmd, size=14):
    return t(x, y, f'<tspan class="usr">{USER}</tspan><tspan class="dim">:~$ </tspan><tspan class="txt">{e(cmd)}</tspan>', "txt", size)


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
{t(x, y, f'<tspan class="usr">{USER}</tspan><tspan class="dim">:~$ </tspan>', "txt", size)}
<g clip-path="url(#{cid})">{t(x0, y, e(cmd), "txt", size)}</g>"""


def caret(x, y, size=14, extra=""):
    return f'<rect class="blink" x="{x}" y="{y - size + 2}" width="{CW * size:.1f}" height="{size + 1}" fill="{AMBER}" {extra}/>'


def label(x, y, s, right="", w=W):
    """Linha de contexto em cinza: caminho à esquerda, estado à direita."""
    out = t(x, y, e(s), "dim", 12)
    if right:
        out += t(w, y, e(right), "dim", 12, 'text-anchor="end"')
    return out


# ---------------------------------------------------------------------------
# Logo ANSI Shadow desenhado como vetor (não depende da fonte do leitor)
# ---------------------------------------------------------------------------

GLYPHS = {
    "0": [" ██████╗ ", "██╔═████╗", "██║██╔██║", "████╔╝██║", "╚██████╔╝", " ╚═════╝ "],
    "P": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "1": [" ██╗", "███║", "╚██║", " ██║", " ██║", " ╚═╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "X": ["██╗  ██╗", "╚██╗██╔╝", " ╚███╔╝ ", " ██╔██╗ ", "██╔╝ ██╗", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
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
    return (f'<path d="{"".join(lines)}" fill="none" stroke="{LOGO_SHADOW}" stroke-opacity=".6" stroke-width="1.3"/>'
            f'<path d="{"".join(blocks)}" fill="{LOGO}"/>'), len(rows[0]) * cw


# ---------------------------------------------------------------------------
# Painéis: sem moldura, tudo alinhado à mesma margem esquerda (x = 0), para
# que o texto pareça escrito direto na página do GitHub.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Imagem em ASCII colorido: PNG transparente, JPG de fundo branco ou GIF animado.
# Cada célula vira um caractere escolhido pela luminância e pintado com a cor
# média daquele pedaço da imagem (reduzida a poucas cores, para o SVG não
# virar uma tspan por letra). Uma imagem parada aparece linha a linha, como um
# render; um GIF vira um quadro por <g>, alternados por CSS (step-end), o que
# funciona dentro de <img> no GitHub, ao contrário de JavaScript.
def header():
    p = []
    boot = [
        "montando /dev/dados",
        "carregando modelos ........ python · keras · scikit-learn",
        "compilando interface ...... react · webgl · gsap",
        "iniciando simulador ....... haskell",
    ]
    for i, msg in enumerate(boot):
        p.append(t(0, 14 + i * 19, f'<tspan class="dim">[ </tspan><tspan class="usr">ok</tspan><tspan class="dim"> ]</tspan> {e(msg)}',
                   "txt a", 12, delay(0.25 + i * 0.3)))

    p.append(typed(0, 108, "./peterson --init", 1.6))

    logo, lw = ansi_logo("0PH1S", 0, 128, 12, 22)
    ah = 6 * 22
    p.append(f'<g class="on glow" {delay(2.8)}>{logo}</g>')

    # bloco estilo neofetch ao lado do logo, centrado na altura dele
    ix, vx = round(lw) + 80, round(lw) + 162
    top = round(128 + ah / 2 - 66)
    info = [
        ("nome", "Peterson Carara"),
        ("curso", "Ciência de Dados"),
        ("campus", "FATEC Baixada Santista"),
        ("local", "Brasil"),
        ("shell", "python · js · haskell"),
        ("foco", "dados · web · baixo nível"),
    ]
    g = [t(ix, top, '<tspan class="usr">peterson</tspan><tspan class="dim">@</tspan><tspan class="amb">0ph1s</tspan>', "txt", 14),
         t(ix, top + 16, "-" * 14, "dim", 14)]
    for i, (k, v) in enumerate(info):
        y = top + 38 + i * 19
        g.append(t(ix, y, e(k), "dim", 13))
        g.append(t(vx, y, e(v), "hot" if k == "nome" else "txt", 13))
    for i, c in enumerate(SWATCH):
        g.append(f'<rect x="{ix + i * 26}" y="{top + 38 + 6 * 19 - 6}" width="22" height="12" fill="{c}"/>')
    p.append(f'<g class="a" {delay(3.2)}>{"".join(g)}</g>')

    ty = round(128 + ah + 68)
    p.append(t(0, ty, "Transformo dados em decisões e ideias em interfaces.", "hot glow a", 21, delay(3.6)))
    p.append(f'<g class="a" {delay(4.0)}>{prompt(0, ty + 54, "")}{caret((len(USER) + 4) * CW * 14, ty + 54)}</g>')
    h = ty + 66
    return svg(h, "\n".join(p), "0PH1S em ASCII. Peterson Carara, estudante de Ciência de Dados na FATEC Baixada Santista. "
                                 "Transformo dados em decisões e ideias em interfaces.")


def strip(cmd, right=""):
    """Um prompt sozinho, usado como título de seção."""
    p = [prompt(0, 16, cmd)]
    if right:
        p.append(label(0, 16, "", right))
    return svg(24, "\n".join(p), f"{USER}:~$ {cmd}")


def flags(x, y, items, kw=150, lh=22):
    out = []
    for i, (k, v) in enumerate(items):
        out.append(t(x, y + i * lh, e(k), "amb", 12.5))
        out.append(t(x + kw, y + i * lh, e(v), "dim", 12.5))
    return "\n".join(out)


def art(x, y, lines, size=13, lh=15.5):
    return "\n".join(t(x, y + i * lh, e(l), "amb", size, 'xml:space="preserve"') for i, l in enumerate(lines))


def stack():
    h = 330
    rx = 480                       # coluna da direita
    p = [prompt(0, 16, "tmux attach -t stack"), label(0, 16, "", "3 painéis")]

    # data science, à esquerda
    p.append(label(0, 56, "~/stack/data-science", "model: ready", w=430))
    chart = [
        "▲",
        "│                · ╭──",
        "│          ·  ·╭──╯·",
        "│       ·  ╭──╯  ·",
        "│    · ╭──╯·",
        "│  ·╭──╯  ·",
        "│╭──╯·",
        "└─────────────────────▶",
    ]
    p.append(f'<g class="glow">{art(0, 86, chart)}</g>')
    p.append(t(214, 112, "Data Science", "hot glow", 24))
    p.append(t(214, 136, "modelos que encontram", "txt", 12.5))
    p.append(t(214, 154, "padrões e antecipam", "txt", 12.5))
    p.append(t(214, 172, "o que vem a seguir.", "txt", 12.5))
    p.append(flags(0, 228, [
        ("--machine-learning", "redes neurais, KerasTuner"),
        ("--estatistica", "Kruskal-Wallis, Mann-Whitney"),
        ("--reducao-dim", "PCA e atributos"),
        ("--analise", "pandas, scikit-learn, R"),
        ("--notebooks", "Jupyter, visualização"),
    ], kw=170))

    # web e pesquisa, à direita
    p.append(label(rx, 56, "~/stack/web", "build: passing"))
    p.append(t(rx, 88, "Web", "hot", 22))
    p.append(t(rx + 66, 88, "rápida, imersiva e acessível", "dim", 12))
    p.append(flags(rx, 118, [
        ("--react", "vite · tailwind"),
        ("--imersivo", "webgl · shaders · gsap"),
        ("--backend", "django · mysql"),
    ], kw=120))

    p.append(label(rx, 206, "~/stack/pesquisa", "sim: running"))
    p.append(t(rx, 238, "Pesquisa", "hot", 22))
    p.append(t(rx + 126, 238, "o que há abaixo da abstração", "dim", 12))
    p.append(flags(rx, 268, [
        ("--haskell", "FSM de aviônica de UAV"),
        ("--ic", "iniciação científica, FATEC"),
        ("--latex", "artigos e relatórios"),
    ], kw=120))
    return svg(h, "\n".join(p), "Stack: Data Science (machine learning, estatística, PCA, pandas, scikit-learn), "
                                "Web (React, WebGL, GSAP, Django) e Pesquisa (Haskell, iniciação científica, LaTeX).")


SIGNALS = ["▁▂▃▅▇▅▃▂▁▂▃▅", "▂▄▆█▆▄▂▄▆█▆▄", "▇▅▃▁▃▅▇▅▃▁▃▅", "▁▃▆▃▁▃▆▃▁▃▆▃", "▅▅▇▇▃▃▅▅▇▇▃▃", "▁▁▂▃▅█▅▃▂▁▁▂"]


def card(i, repo, title, desc, stack, tag):
    w, h = 430, 160
    p = [
        t(0, 14, f'<tspan class="amb" font-weight="700">CH{i}</tspan>  {e(tag)}', "dim", 12),
        f'<rect class="blink" x="{w - 38}" y="6" width="7" height="7" fill="{LIVE}"/>',
        t(w, 14, "live", "dim", 12, 'text-anchor="end"'),
        t(0, 44, e(title), "hot glow", 17),
    ]
    for j, line in enumerate(textwrap.wrap(desc, 58)[:3]):
        p.append(t(0, 68 + j * 17, e(line), "txt", 12))
    p.append(t(0, 128, '<tspan class="dim">stack </tspan>' + e(stack), "amb", 12))
    p.append(t(w, 128, SIGNALS[(i - 1) % len(SIGNALS)], "amb", 12, 'text-anchor="end" opacity=".7"'))
    p.append(t(0, 150, "&gt; OPEN_REPO ↗", "amb", 12, 'font-weight="700"'))
    p.append(t(w, 150, e(f"0ph1s/{repo}"[:44]), "dim", 11, 'text-anchor="end"'))
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
    h = 384
    lx = 330                       # coluna das linguagens
    p = [prompt(0, 16, "./diagnostico --github"), label(0, 16, "", f"snapshot {date.today():%d.%m.%Y}")]

    # coluna esquerda: leitura do sistema
    rows = [
        ("REPOS", f"{d['repos']} públicos"),
        ("STARS", str(d["stars"])),
        ("FOLLOWERS", str(d["followers"])),
        ("CONTRIB 12M", str(d["contrib"])),
        ("UPTIME", f"desde {d['since']}"),
        ("SYSTEM", "ONLINE"),
    ]
    p.append(label(0, 56, "~/sistema"))
    for i, (k, v) in enumerate(rows):
        y = 82 + i * 22
        p.append(t(0, y, k, "dim", 12.5))
        p.append(t(270, y, e(v), "hot", 12.5, 'text-anchor="end"'))
        p.append(f'<line x1="{len(k) * CW * 12.5 + 8:.1f}" y1="{y - 4}" x2="{270 - len(v) * CW * 12.5 - 8:.1f}" y2="{y - 4}" '
                 f'stroke="{WIRE}" stroke-dasharray="1 4"/>')
    p.append(f'<rect class="led" x="{270 - 6 * CW * 12.5 - 16:.1f}" y="{82 + 5 * 22 - 8}" width="7" height="7" fill="{LIVE}" filter="url(#glow)"/>')

    # coluna direita: linguagens como barras de blocos
    top = d["langs"][:6]
    total = sum(v for _, v in d["langs"]) or 1
    cells = 24
    p.append(label(lx, 56, "~/linguagens"))
    for i, (name, size) in enumerate(top):
        y = 82 + i * 22
        pct = size / total
        full = round(pct * cells)
        p.append(t(lx, y, e(name.lower().replace(" notebook", "")[:14]), "txt", 12.5))
        # cada célula é um "█" desenhado como retângulo, para não depender da fonte
        for c in range(cells):
            on = c < full
            p.append(f'<rect x="{lx + 120 + c * 13}" y="{y - 11}" width="11" height="13" fill="{AMBER if on else WIRE_2}"'
                     f'{" filter=\"url(#glow)\"" if on else ""}/>')
        p.append(t(W, y, f"{pct * 100:4.1f}%", "dim", 12.5, 'text-anchor="end"'))

    # mapa de contribuições das últimas 53 semanas
    y0 = 248
    p.append(label(0, y0 - 14, "~/atividade · últimas 53 semanas"))
    weeks = d["weeks"][-53:]
    peak = max((c for w in weeks for c in w), default=0) or 1
    step = W / 53
    size = step - 3
    for wi, week in enumerate(weeks):
        for di, c in enumerate(week):
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            p.append(f'<rect x="{wi * step:.1f}" y="{y0 + di * (size + 3):.1f}" width="{size:.1f}" height="{size:.1f}" '
                     f'rx="2" fill="{HEAT[lvl]}"/>')
    ly = y0 + 7 * (size + 3) + 14
    p.append(t(W - 5 * 16 - 40, ly, "menos", "dim", 11, 'text-anchor="end"'))
    for i, c in enumerate(HEAT):
        p.append(f'<rect x="{W - 5 * 16 - 32 + i * 16}" y="{ly - 9}" width="11" height="11" rx="2" fill="{c}"/>')
    p.append(t(W, ly, "mais", "dim", 11, 'text-anchor="end"'))
    return svg(h, "\n".join(p), f"Diagnóstico: {d['repos']} repositórios públicos, {d['stars']} estrelas, "
                                f"{d['followers']} seguidores, {d['contrib']} contribuições em 12 meses. "
                                f"Linguagens: {', '.join(n for n, _ in top)}.")


def footer():
    h = 104
    p = [
        prompt(0, 16, "exit"),
        t(0, 40, "logout", "dim", 13),
        t(0, 62, "Connection to 0ph1s closed. Obrigado pela visita.", "txt", 13),
        prompt(0, 94, ""),
        caret((len(USER) + 4) * CW * 14, 94),
        label(0, 94, "", "~ fim da transmissão ~"),
    ]
    return svg(h, "\n".join(p), "exit. Obrigado pela visita.")


def render(data):
    files = {
        "header.svg": header(),
        "stack.svg": stack(),
        "footer.svg": footer(),
        "cmd-projetos.svg": strip("git log --author=0ph1s", "6 canais"),
        "diag.svg": diag(data),
    }
    for i, prj in enumerate(PROJECTS, 1):
        files[f"ch{i}.svg"] = card(i, *prj)
    return files


def main(themes=("dark", "light")):
    data = github_data()
    for theme in themes:
        use(theme)
        out = OUT / theme
        out.mkdir(parents=True, exist_ok=True)
        files = render(data)
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
        print("ok", theme, len(files), "arquivos")


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("dark", "light"))
