import sys
out = sys.argv[1]
W, H = 840, 384
CW = 8.4  # fixed character pitch for typed commands
THEMES = {
 "dark":  dict(bg="#0d1117", bar="#161b22", border="#30363d", text="#e6edf3", dim="#8b949e",
               accent="#3fb950", ramp=["#aff5b4","#7ee787","#56d364","#3fb950","#2ea043","#238636","#196c2e"],
               dots=["#ff7b72","#d29922","#3fb950"]),
 "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", text="#1f2328", dim="#656d76",
               accent="#1a7f37", ramp=["#4ac26b","#2da44e","#1f883d","#1a7f37","#116329","#0f5323","#044f1e"],
               dots=["#cf222e","#9a6700","#1a7f37"]),
}
I = ["#####","..#..","..#..","..#..","..#..","..#..","#####"]
S = [".####","#....","#....",".###.","....#","....#","####."]
INFO = [("role","Product engineer"),("focus","0→1 and 1→100, end to end"),("now","building"),
        ("stack","TypeScript · Python · Go"),("with","Next.js · FastAPI · PostgreSQL"),
        ("based","India"),("freelance","Top Rated on Upwork")]

def typed(cmd, x, y, start, step, cls="t"):
    s = []
    for i, ch in enumerate(cmd):
        if ch == " ": continue
        s.append(f'<text class="{cls} ch" x="{x+i*CW:.1f}" y="{y}" style="animation-delay:{start+i*step:.2f}s">{ch}</text>')
    return "\n".join(s)

def build(t):
    c = THEMES[t]
    p = []
    p.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
<title id="title">Ishaan2053: product engineer, 0 to 1 and 1 to 100</title>
<desc id="desc">A terminal window running whoami. Role: product engineer. Focus: 0 to 1 and 1 to 100, end to end. Now: building. Stack: TypeScript, Python, Go, Next.js, FastAPI, PostgreSQL. Based in India. Top Rated on Upwork.</desc>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:14px}}
.t{{fill:{c["text"]}}}.d{{fill:{c["dim"]}}}.a{{fill:{c["accent"]}}}.b{{font-weight:700}}
.ch{{opacity:0;animation:show .01s linear forwards}}
.in{{opacity:0;animation:rise .35s ease-out forwards}}
.px{{opacity:0;animation:show .25s ease-out forwards}}
.cur{{opacity:0;animation:show .01s linear 3.2s forwards,move 1.2s steps(12,end) 3.6s forwards,blink 1.1s steps(1,end) 5s infinite}}
@keyframes show{{to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:none}}}}
@keyframes move{{to{{transform:translateX({12*CW:.1f}px)}}}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.ch,.in,.px{{animation:none;opacity:1}}.cur{{animation:none;opacity:1;transform:translateX({12*CW:.1f}px)}}}}
</style>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>
<path d="M.5 38V10.5a10 10 0 0 1 10-10h{W-21}a10 10 0 0 1 10 10V38z" fill="{c["bar"]}" stroke="{c["border"]}"/>
<circle cx="22" cy="19" r="5.5" fill="{c["dots"][0]}"/><circle cx="42" cy="19" r="5.5" fill="{c["dots"][1]}"/><circle cx="62" cy="19" r="5.5" fill="{c["dots"][2]}"/>
<text class="d" x="{W/2}" y="24" text-anchor="middle" font-size="13">Ishaan2053@github: ~</text>''')
    # first command
    x0, y = 32, 74
    p.append(f'<text class="a b" x="{x0}" y="{y}">$</text>')
    p.append(typed("whoami", x0+2*CW, y, 0.5, 0.1))
    # monogram
    cell, gx, gy = 16, 36, 108
    for r in range(7):
        for gi, glyph in enumerate((I, S)):
            for col, ch in enumerate(glyph[r]):
                if ch == "#":
                    x = gx + (gi*6 + col)*cell
                    p.append(f'<rect class="px" x="{x}" y="{gy+r*cell}" width="{cell-3}" height="{cell-3}" rx="2" fill="{c["ramp"][r]}" style="animation-delay:{1.35+r*0.06+col*0.02:.2f}s"/>')
    # info
    ix, kx, iy, lh = 260, 352, 116, 24
    d0 = 1.4
    p.append(f'<g class="in" style="animation-delay:{d0}s"><text x="{ix}" y="{iy}"><tspan class="a b">Ishaan2053</tspan><tspan class="d">@</tspan><tspan class="a b">github</tspan></text>'
             f'<rect x="{ix}" y="{iy+9}" width="143" height="1" fill="{c["border"]}"/></g>')
    for i, (k, v) in enumerate(INFO):
        yy = iy + 14 + (i+1)*lh
        p.append(f'<g class="in" style="animation-delay:{d0+0.12*(i+1):.2f}s"><text class="a b" x="{ix}" y="{yy}">{k}</text><text class="t" x="{kx}" y="{yy}">{v}</text></g>')
    sy = iy + 14 + (len(INFO)+1)*lh - 10
    sw = "".join(f'<rect x="{ix+i*22}" y="{sy}" width="22" height="12" fill="{col}"/>' for i, col in enumerate(c["ramp"]))
    p.append(f'<g class="in" style="animation-delay:{d0+0.12*(len(INFO)+1):.2f}s">{sw}</g>')
    # second command
    y2 = H - 28
    p.append(f'<g class="ch" style="animation-delay:3.2s"><text class="a b" x="{x0}" y="{y2}">$</text></g>')
    p.append(typed("ls ~/shipped", x0+2*CW, y2, 3.6, 0.1))
    p.append(f'<rect class="cur" x="{x0+2*CW:.1f}" y="{y2-13}" width="8" height="17" fill="{c["accent"]}"/>')
    p.append("</svg>")
    return "\n".join(p)

for t in THEMES:
    open(f"{out}/hero-{t}.svg", "w", encoding="utf-8").write(build(t))
