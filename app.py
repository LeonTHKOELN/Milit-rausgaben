"""Verteidigungsausgaben Deutschland 2014–2026e.

Streamlit-App auf Basis des NATO-Berichts „Defence Expenditure of NATO Countries“
(2026) und der SIPRI Military Expenditure Database (v1.2, April 2026).
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"

ZIEL_KERN = 3.5      # Hague-Ziel für Kernausgaben bis 2035, % des BIP
ZIEL_ALT = 2.0       # bisheriges NATO-Ziel, % des BIP
RICHTWERT_EQ = 20.0  # NATO-Richtwert Ausrüstungsquote, % der Kernausgaben

KATEGORIEN = {
    "ausruestung": "Ausrüstung",
    "personal": "Personal",
    "infrastruktur": "Infrastruktur",
    "sonstige": "Sonstiges",
}
FARBEN = {
    "ausruestung": "#b5482f",
    "personal": "#2f6fb5",
    "infrastruktur": "#3f9a5a",
    "sonstige": "#c9962b",
}
GRAU = "#a8a49c"
SCHAETZUNG = "rgba(150,150,150,0.12)"

st.set_page_config(page_title="Verteidigungsausgaben Deutschland", page_icon="📊", layout="wide")


# ---------------------------------------------------------------- Hilfsfunktionen
def fde(x: float, d: int = 1) -> str:
    """Zahl im deutschen Format."""
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def jahr_label(j: int) -> str:
    return f"{j}e" if j >= 2025 else str(j)


Q_NATO = "https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2026-en.pdf"
Q_NATO_T1 = f"[NATO: Defence Expenditure of NATO Countries 2026, Tabelle 1 (Kernausgaben, nominal in Landeswährung)]({Q_NATO})"
Q_NATO_T3 = f"[NATO: Defence Expenditure of NATO Countries 2026, Tabelle 3 (Anteil am realen BIP und reale Veränderung zum Vorjahr)]({Q_NATO})"
Q_SIPRI = ("[SIPRI Military Expenditure Database, Datensatz 1949–2025, Version 1.2 (Excel)]"
           "(https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2025_v1.2.xlsx)")


def quellen(*eintraege: str) -> None:
    """Ausklappbare Quellenangabe unter einem Diagramm."""
    with st.expander("Quellen"):
        st.markdown("\n".join(f"- {e}" for e in eintraege))


@st.cache_data
def lade_daten():
    g = pd.read_csv(DATA / "germany.csv")
    v = pd.read_csv(DATA / "vergleich.csv")
    a = pd.read_csv(DATA / "allies.csv")
    t = pd.read_csv(DATA / "bip_trend.csv")
    s = pd.read_csv(DATA / "sipri_de.csv").dropna(subset=["anteil_bip_pct"])
    aa = pd.read_csv(DATA / "abgleich_alliierte.csv")
    bh = pd.read_csv(DATA / "bundeshaushalt.csv")
    bh["anteil_epl14"] = bh.epl14_mrd / bh.bund_mrd * 100
    bh["anteil_mit_sv"] = (bh.epl14_mrd + bh.sv_bw_mrd) / bh.bund_mrd * 100
    for k in KATEGORIEN:
        g[f"{k}_real"] = g["real_eur"] * g[k] / 1e5  # Mrd. €, Preise 2021
    return g, v, a, t, s, aa, bh


def layout(fig: go.Figure, hoehe: int = 380, y_titel: str | None = None, schaetzung: bool = True) -> go.Figure:
    if schaetzung:
        fig.add_vrect(x0=2024.5, x1=2026.5, fillcolor=SCHAETZUNG, line_width=0,
                      annotation_text="Schätzung", annotation_position="top left")
    fig.update_layout(
        height=hoehe, margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified", separators=",.",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis_title=y_titel,
    )
    fig.update_xaxes(dtick=2 if schaetzung else None)
    return fig


g, v, a, t, s, aa, bh = lade_daten()
J = g.set_index("jahr")
S = s.set_index("jahr")
a14, a23, a24, a26 = J.loc[2014], J.loc[2023], J.loc[2024], J.loc[2026]
anstieg = a26.real_eur - a14.real_eur


def rang(spalte: str) -> int:
    return int(a.sort_values(spalte, ascending=False).reset_index(drop=True).query("land == 'Deutschland'").index[0]) + 1


# ---------------------------------------------------------------- Kopf
st.title("Verteidigungsausgaben Deutschland 2014–2026")
st.markdown(
    f"Deutschland gibt 2026 real das **{fde(a26.real_eur / a14.real_eur, 2)}-Fache** von 2014 aus, "
    f"und **{fde((a26.real_eur - a23.real_eur) / anstieg * 100, 0)} %** dieses Anstiegs entfallen auf die Jahre nach 2023. "
    f"Für die Industrie zählt vor allem die Ausrüstung: Sie wächst real auf das "
    f"**{fde(a26.ausruestung_real / a14.ausruestung_real, 1)}-Fache**, während die Zahl der Soldatinnen und Soldaten fast gleich bleibt."
)

k = st.columns(5)
k[0].metric("Ausgaben real, 2026e", f"{fde(a26.real_eur / 1e3)} Mrd. €",
            f"{fde((a26.real_eur / a14.real_eur - 1) * 100, 0)} % ggü. 2014", help="Preise von 2021")
k[1].metric("Anteil am BIP, 2026e", f"{fde(a26.anteil_bip, 2)} %",
            f"{fde(a26.anteil_bip - a14.anteil_bip, 2)} Pp. ggü. 2014")
k[2].metric("Ausrüstung real, 2026e", f"{fde(a26.ausruestung_real)} Mrd. €",
            f"2014: {fde(a14.ausruestung_real)} Mrd. €", delta_color="off", help="Eigene Berechnung")
k[3].metric("Ausrüstungsquote, 2026e", f"{fde(a26.ausruestung)} %",
            f"2014: {fde(a14.ausruestung)} %", delta_color="off")
k[4].metric("Militärpersonal, 2026e", f"{fde(a26.personal_tsd)} Tsd.",
            f"{fde((a26.personal_tsd / a14.personal_tsd - 1) * 100)} % ggü. 2014")

tabs = st.tabs(["Entwicklung", "BIP-Anteil", "Kategorien & Personal", "Bundeshaushalt", "Abgleich SIPRI",
                "Langfristvergleich", "Einordnung", "Daten & Quellen"])

# ---------------------------------------------------------------- Entwicklung
with tabs[0]:
    st.subheader("Der Anstieg ist ein Sprung seit 2024 und stützt sich stark auf Schätzjahre")
    c1, c2 = st.columns(2)
    with c1:
        preis = (a26.nominal_eur / a26.real_eur - 1) * 100
        st.markdown("**Nominal und real, in Mrd. €**")
        st.caption(f"Im Wert für 2026 steckt gegenüber 2021 ein Preiseffekt von {fde(preis)} %, "
                   "deshalb liegt der nominale Wert deutlich höher.")
        fig = go.Figure()
        fig.add_scatter(x=g.jahr, y=g.nominal_eur / 1e3, name="Nominal", line=dict(color=FARBEN["personal"], width=2))
        fig.add_scatter(x=g.jahr, y=g.real_eur / 1e3, name="Real (Preise 2021)", line=dict(color=FARBEN["ausruestung"], width=3))
        fig.update_traces(hovertemplate="%{y:.1f} Mrd. €")
        st.plotly_chart(layout(fig, y_titel="Mrd. €"), width="stretch")
        with st.expander("Was bedeuten nominal, real und Preiseffekt?"):
            st.markdown(
                f"- **Nominal:** Die Ausgaben in den Preisen des jeweiligen Jahres.\n"
                f"- **Real:** Die Ausgaben in Preisen von 2021. So zeigt die Kurve die Entwicklung ohne allgemeine Preissteigerungen.\n"
                f"- **Preiseffekt:** Das Verhältnis von nominal zu real. 2026: {fde(a26.nominal_eur / 1e3)} Mrd. € geteilt durch "
                f"{fde(a26.real_eur / 1e3)} Mrd. € ergibt {fde(preis)} % gegenüber 2021.\n\n"
                "Im Basisjahr 2021 sind beide Werte gleich, davor liegt der nominale Wert unter dem realen. "
                "Der Preiseffekt ist aus den NATO-Zahlen abgeleitet; die NATO weist ihn nicht aus. "
                "Wie die Bereinigung genau berechnet wird, geht aus den Tabellen nicht hervor."
            )
    with c2:
        st.markdown("**Reale Veränderung zum Vorjahr, in %**")
        st.caption(f"{fde((a26.real_eur - a24.real_eur) / anstieg * 100, 0)} % des gesamten realen Anstiegs seit 2014 "
                   "beruhen auf den Schätzwerten für 2025 und 2026.")
        fig = go.Figure(go.Bar(
            x=g.jahr, y=g.real_aend, hovertemplate="%{y:.2f} %<extra></extra>",
            marker_color=[FARBEN["personal"] if j >= 2025 else FARBEN["ausruestung"] for j in g.jahr]))
        st.plotly_chart(layout(fig, y_titel="%", schaetzung=False).update_xaxes(dtick=2), width="stretch")

# ---------------------------------------------------------------- BIP-Anteil
with tabs[1]:
    st.subheader("Beim BIP-Anteil hat Deutschland aufgeholt, liegt aber noch deutlich unter dem Hague-Ziel")
    luecke_pp = ZIEL_KERN - a26.anteil_bip
    luecke_usd = (ZIEL_KERN / 100 * a26.bip_real_usd - a26.real_usd) / 1e3
    st.caption(f"Zum Ziel von {fde(ZIEL_KERN)} % bis 2035 fehlen {fde(luecke_pp, 2)} Prozentpunkte; beim BIP von 2026 "
               f"wären das rund {fde(luecke_usd, 0)} Mrd. US-$ (Preise von 2021). Alle Werte sind Kernausgaben ohne den 1,5-%-Topf.")
    fig = go.Figure()
    reihen = [("frankreich", "Frankreich", GRAU), ("vereinigtes_koenigreich", "UK", GRAU), ("usa", "USA", GRAU),
              ("polen", "Polen", GRAU), ("nato_eu_kanada", "NATO Europa/Kanada", FARBEN["personal"])]
    for key, name, col in reihen:
        fig.add_scatter(x=v.jahr, y=v[key], name=name, line=dict(color=col, width=1.5))
    fig.add_scatter(x=g.jahr, y=g.anteil_bip, name="Deutschland", line=dict(color=FARBEN["ausruestung"], width=4))
    fig.add_hline(y=ZIEL_KERN, line_dash="dash", line_color="#777", annotation_text=f"Hague-Ziel 2035: {fde(ZIEL_KERN)} %")
    fig.add_hline(y=ZIEL_ALT, line_dash="dot", line_color="#777", annotation_text=f"Bisheriges Ziel: {fde(ZIEL_ALT, 0)} %")
    fig.update_traces(hovertemplate="%{y:.2f} %")
    st.plotly_chart(layout(fig, 430, "% des BIP"), width="stretch")

    st.markdown("**BIP-Anteil je Land, 2014–2026e**")
    st.caption(f"Sortiert nach dem Wert für 2026e, alle Länder auf derselben Skala. Deutschland steht 2026 auf Platz "
               f"{rang('anteil_bip_2026')} von {len(a)}; 2014 war es Platz {rang('anteil_bip_2014')}. "
               "Graue Linie: Deutschland zum Vergleich.")
    reihenfolge = t[t.jahr == 2026].sort_values("anteil", ascending=False).land.tolist()
    auswahl = st.multiselect("Länder auswählen (leer = alle)", reihenfolge, default=[])
    laender = auswahl or reihenfolge
    de = t[t.land == "Deutschland"]
    spalten = 4
    ymax = float(t.anteil.max()) * 1.05
    for i in range(0, len(laender), spalten):
        cols = st.columns(spalten)
        for c, land in zip(cols, laender[i:i + spalten]):
            d = t[t.land == land]
            f = go.Figure()
            f.add_vrect(x0=2024.5, x1=2026.5, fillcolor=SCHAETZUNG, line_width=0)
            for y in (ZIEL_ALT, ZIEL_KERN):
                f.add_hline(y=y, line_dash="dot", line_width=1, line_color="#999")
            if land != "Deutschland":
                f.add_scatter(x=de.jahr, y=de.anteil, line=dict(color=GRAU, width=1), name="Deutschland",
                              hovertemplate="Deutschland: %{y:.2f} %<extra></extra>")
            f.add_scatter(x=d.jahr, y=d.anteil, line=dict(color=FARBEN["ausruestung"], width=3 if land == "Deutschland" else 2),
                          name=land, hovertemplate=land + ": %{y:.2f} %<extra></extra>")
            f.update_layout(height=170, margin=dict(l=5, r=5, t=28, b=5), showlegend=False, separators=",.",
                            title=dict(text=f"{reihenfolge.index(land) + 1}. {land}: {fde(d.anteil.iloc[-1], 2)} %",
                                       font=dict(size=13)), hovermode="x unified")
            f.update_yaxes(range=[0, ymax], dtick=2)
            f.update_xaxes(tickvals=[2014, 2026], ticktext=["2014", "2026e"])
            c.plotly_chart(f, width="stretch", key=f"mini_{land}")

# ---------------------------------------------------------------- Kategorien & Personal
with tabs[2]:
    st.subheader("Das zusätzliche Geld fließt in Ausrüstung und Betrieb, kaum in Personal")
    with st.expander("Was bedeuten die Kategorien?"):
        st.markdown(
            "- **Ausrüstung:** Großgerät sowie Forschung und Entwicklung für Großgerät.\n"
            "- **Personal:** Ausgaben für militärisches und ziviles Personal sowie Pensionen.\n"
            "- **Infrastruktur:** NATO-Gemeinschaftsinfrastruktur und nationaler militärischer Bau.\n"
            "- **Sonstiges:** Betrieb und Instandhaltung, übrige Forschung und Entwicklung sowie Kernausgaben, "
            "die keiner der anderen Kategorien zugeordnet sind.\n\n"
            "Alle vier Kategorien zählen zu den Kernausgaben (core defence expenditure). Die Investitionen aus dem "
            "1,5-%-Topf gehören nicht dazu, Zivilschutz schließt die NATO ausdrücklich aus. Die NATO schlüsselt "
            "„Sonstiges“ nicht weiter auf; siehe dazu den Reiter „Einordnung“. "
            "Quelle: NATO-Bericht 2026, Tabellen 8a und 8b sowie Definition."
        )
    zuwachs = {kk: (a26[f"{kk}_real"] - a14[f"{kk}_real"]) / (anstieg / 1e3) * 100 for kk in KATEGORIEN}
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ausgaben nach Kategorie, real in Mrd. €**")
        st.caption("Vom realen Anstieg seit 2014 entfallen " + ", ".join(
            f"{fde(zuwachs[kk], 0)} % auf {n}" for kk, n in KATEGORIEN.items()) + ".")
        fig = go.Figure()
        for kk, n in KATEGORIEN.items():
            fig.add_bar(x=g.jahr, y=g[f"{kk}_real"], name=n, marker_color=FARBEN[kk], hovertemplate="%{y:.1f} Mrd. €")
        st.plotly_chart(layout(fig.update_layout(barmode="stack"), y_titel="Mrd. € (Preise 2021)", schaetzung=False)
                        .update_xaxes(dtick=2), width="stretch")
    with c2:
        st.markdown("**Ausgaben nach Kategorie, in % der Kernausgaben**")
        st.caption(f"Die Ausrüstung wächst von {fde(a14.ausruestung)} auf {fde(a26.ausruestung)} %, das Personal sinkt "
                   f"von {fde(a14.personal)} auf {fde(a26.personal)} %. NATO-Richtwert Ausrüstung: {fde(RICHTWERT_EQ, 0)} %.")
        fig = go.Figure()
        for kk, n in KATEGORIEN.items():
            fig.add_bar(x=g.jahr, y=g[kk], name=n, marker_color=FARBEN[kk], text=g[kk].round(0).astype(int),
                        textposition="inside", hovertemplate="%{y:.2f} %")
        st.plotly_chart(layout(fig.update_layout(barmode="stack"), y_titel="%", schaetzung=False)
                        .update_xaxes(dtick=2), width="stretch")

    c3, c4 = st.columns(2)
    idx = pd.DataFrame({"jahr": g.jahr})
    for kk in KATEGORIEN:
        idx[kk] = g[f"{kk}_real"] / a14[f"{kk}_real"] * 100
    idx["gesamt"] = g.real_eur / a14.real_eur * 100
    idx["militaer"] = g.personal_tsd / a14.personal_tsd * 100
    i26 = idx.set_index("jahr").loc[2026]
    je14, je26 = a14.real_eur / a14.personal_tsd, a26.real_eur / a26.personal_tsd
    with c3:
        st.markdown("**Index: Ausgaben je Kategorie und Militärpersonal (2014 = 100)**")
        st.caption(f"Gesamte reale Kernausgaben je Soldat oder Soldatin: {fde(je14, 0)} Tsd. € in 2014, "
                   f"{fde(je26, 0)} Tsd. € in 2026e.")
        fig = go.Figure()
        serien = [("ausruestung", "Ausrüstung", FARBEN["ausruestung"], 3), ("infrastruktur", "Infrastruktur", FARBEN["infrastruktur"], 2),
                  ("sonstige", "Sonstiges", FARBEN["sonstige"], 2), ("gesamt", "Gesamt", "#222", 3),
                  ("personal", "Personalausgaben", FARBEN["personal"], 2), ("militaer", "Militärpersonal", GRAU, 2)]
        for key, n, col, w in serien:
            fig.add_scatter(x=idx.jahr, y=idx[key], name=n, line=dict(color=col, width=w), hovertemplate="%{y:.0f}")
        st.plotly_chart(layout(fig, 420, "Index"), width="stretch")
        with st.expander("Wie liest man den Index?"):
            st.markdown(
                "- **Index:** Jede Reihe wird durch ihren Wert von 2014 geteilt und mal 100 genommen. So lassen sich "
                "Euro und Personenzahlen auf einer Skala vergleichen.\n"
                f"- **Lesebeispiel:** 2026e stehen die Ausrüstung bei {fde(i26.ausruestung, 0)}, die Infrastruktur bei "
                f"{fde(i26.infrastruktur, 0)}, Sonstiges bei {fde(i26.sonstige, 0)}, die Gesamtausgaben bei {fde(i26.gesamt, 0)}, "
                f"die Personalausgaben bei {fde(i26.personal, 0)} und das Militärpersonal bei {fde(i26.militaer, 0)}.\n"
                f"- **Kleine Basis:** Die Infrastruktur steigt im Index stark, ihr Betrag bleibt aber klein: real von "
                f"{fde(a14.infrastruktur_real)} auf {fde(a26.infrastruktur_real)} Mrd. €. Der Index zeigt das Tempo, nicht die Größe.\n"
                "- **Personal:** Personalausgaben sind Euro, einschließlich Zivilpersonal und Pensionen. Militärpersonal ist "
                "die Zahl der Soldatinnen und Soldaten.\n"
                f"- **Je Soldat:** Die gesamten realen Kernausgaben geteilt durch das Militärpersonal: 2026e "
                f"{fde(a26.real_eur / 1e3)} Mrd. € geteilt durch {fde(a26.personal_tsd)} Tsd. ergibt rund {fde(je26, 0)} Tsd. €.\n\n"
                "Das sind nicht die Kosten eines Soldaten oder einer Soldatin, denn im Wert stecken auch Ausrüstung, Betrieb, "
                "Infrastruktur, Zivilpersonal und Pensionen. Die Index- und Je-Soldat-Werte sind eigene Berechnungen aus den NATO-Zahlen."
            )
    with c4:
        st.markdown("**Militärpersonal, in Tausend**")
        st.caption("Aktive Friedensstärke ohne ausgebildete Reserven mit hoher Bereitschaft; 2025 und 2026 sind "
                   "Schätzungen. Quelle: NATO-Tabelle 7.")
        fig = go.Figure(go.Bar(
            x=g.jahr, y=g.personal_tsd, text=[fde(x) for x in g.personal_tsd], textposition="outside",
            marker_color=[FARBEN["personal"] if j >= 2025 else FARBEN["ausruestung"] for j in g.jahr],
            hovertemplate="%{y:.1f} Tsd.<extra></extra>"))
        st.plotly_chart(layout(fig, 420, "Tsd.", schaetzung=False).update_xaxes(dtick=2), width="stretch")

# ---------------------------------------------------------------- Bundeshaushalt
with tabs[3]:
    B = bh.set_index("jahr")
    st.subheader("Der Verteidigungsetat wächst schneller als der Bundeshaushalt")
    st.caption(
        f"Der Anteil des Einzelplans 14 am Bundeshaushalt steigt von {fde(B.loc[2014, 'anteil_epl14'])} % (2014) auf "
        f"{fde(B.loc[2026, 'anteil_epl14'])} % (2026). Mit dem Sondervermögen Bundeswehr entsprechen die Ausgaben 2026 "
        f"{fde(B.loc[2026, 'anteil_mit_sv'])} % des Bundeshaushalts, also rund einem Fünftel.")
    k1, k2, k3 = st.columns(3)
    k1.metric("Einzelplan 14, 2026 (Soll)", f"{fde(B.loc[2026, 'epl14_mrd'])} Mrd. €",
              f"2014: {fde(B.loc[2014, 'epl14_mrd'])} Mrd. €", delta_color="off")
    k2.metric("Bundeshaushalt, 2026 (Soll)", f"{fde(B.loc[2026, 'bund_mrd'])} Mrd. €",
              f"2014: {fde(B.loc[2014, 'bund_mrd'])} Mrd. €", delta_color="off")
    k3.metric("Anteil Einzelplan 14, 2026", f"{fde(B.loc[2026, 'anteil_epl14'])} %",
              f"{fde(B.loc[2026, 'anteil_epl14'] - B.loc[2014, 'anteil_epl14'])} Pp. ggü. 2014")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Anteil am Bundeshaushalt, in %**")
        st.caption("Die gestrichelte Linie zählt das Sondervermögen Bundeswehr hinzu. Es liegt außerhalb des Bundeshaushalts, "
                   "der Wert ist deshalb ein Verhältnis und kein echter Anteil.")
        fig = go.Figure()
        fig.add_scatter(x=bh.jahr, y=bh.anteil_epl14, name="Einzelplan 14", line=dict(color=FARBEN["ausruestung"], width=3),
                        customdata=bh.basis, hovertemplate="%{y:.1f} % (%{customdata})")
        fig.add_scatter(x=bh.jahr, y=bh.anteil_mit_sv, name="Einzelplan 14 + Sondervermögen",
                        line=dict(color=FARBEN["ausruestung"], width=2, dash="dash"), hovertemplate="%{y:.1f} %")
        fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor="rgba(47,111,181,0.08)", line_width=0,
                      annotation_text="Corona-Haushalte", annotation_position="top left")
        st.plotly_chart(layout(fig, 400, "%", schaetzung=False).update_xaxes(dtick=2), width="stretch")
    with c2:
        st.markdown("**Einzelplan 14, Sondervermögen und Bundeshaushalt, in Mrd. €**")
        st.caption("Balken: Verteidigung (linke Achse). Linie: gesamter Bundeshaushalt (rechte Achse).")
        fig = go.Figure()
        fig.add_bar(x=bh.jahr, y=bh.epl14_mrd, name="Einzelplan 14", marker_color=FARBEN["ausruestung"],
                    hovertemplate="%{y:.1f} Mrd. €")
        fig.add_bar(x=bh.jahr, y=bh.sv_bw_mrd, name="Sondervermögen Bundeswehr", marker_color=FARBEN["sonstige"],
                    hovertemplate="%{y:.1f} Mrd. €")
        fig.add_scatter(x=bh.jahr, y=bh.bund_mrd, name="Bundeshaushalt", yaxis="y2",
                        line=dict(color="#222", width=2), hovertemplate="%{y:.1f} Mrd. €")
        fig.update_layout(barmode="stack", yaxis2=dict(overlaying="y", side="right", rangemode="tozero", title="Bundeshaushalt"))
        st.plotly_chart(layout(fig, 400, "Verteidigung, Mrd. €", schaetzung=False).update_xaxes(dtick=2), width="stretch")
    with st.expander("Wie sind die Zahlen zu lesen?"):
        st.markdown(
            "- **Einzelplan 14:** Der Haushalt des Bundesministeriums der Verteidigung, einschließlich Personal und Versorgung. "
            "Er ist nicht dasselbe wie die NATO-Kernausgaben der anderen Reiter: Die NATO zählt zum Beispiel auch das "
            "Sondervermögen und Ausgaben anderer Ressorts mit.\n"
            "- **Soll und Ist:** 2014–2019 und 2026 sind Soll-Werte laut Haushaltsgesetz, 2020–2025 Ist-Werte laut "
            "Haushaltsrechnung. Für 2020–2024 eignen sich Ist-Werte besser, weil Nachtragshaushalte die Soll-Werte stark "
            "verändert haben. Bei einem Soll-Ist-Wechsel sind kleine Sprünge möglich.\n"
            "- **Corona-Jahre:** 2020 und 2021 sinkt der Anteil, weil der Bundeshaushalt durch die Pandemie stark wuchs, "
            "nicht weil weniger für Verteidigung ausgegeben wurde.\n"
            "- **Sondervermögen Bundeswehr:** Ein kreditfinanzierter Topf außerhalb des Bundeshaushalts, seit 2022. "
            "Deshalb steht er in der Grafik getrennt.\n"
            "- **2015:** Der Wert für den Einzelplan 14 ist nicht aus einer Primärquelle geprüft."
        )
    # ---- Gap zwischen NATO-Meldung und Verteidigungshaushalt
    gp = bh.merge(g[["jahr", "nominal_eur"]], on="jahr")
    gp["nato_mrd"] = gp.nominal_eur / 1e3
    gp["gap"] = gp.nato_mrd - gp.epl14_mrd
    gp["rest"] = gp.gap - gp.sv_bw_mrd
    gp["gap_pct"] = gp.gap / gp.nato_mrd * 100
    gp["rest_pct"] = gp.rest / gp.nato_mrd * 100
    gp["epl14_pct"] = gp.epl14_mrd / gp.nato_mrd * 100
    G = gp.set_index("jahr")
    st.subheader("Der Abstand zwischen NATO-Meldung und Verteidigungshaushalt ist stark gewachsen")
    st.caption(
        f"2014 lag die NATO-Meldung {fde(G.loc[2014, 'gap'])} Mrd. € über dem Einzelplan 14, das waren "
        f"{fde(G.loc[2014, 'gap_pct'], 0)} % der gemeldeten Ausgaben. 2025 sind es {fde(G.loc[2025, 'gap'])} Mrd. € "
        f"({fde(G.loc[2025, 'gap_pct'], 0)} %), 2026 laut Plan {fde(G.loc[2026, 'gap'])} Mrd. € ({fde(G.loc[2026, 'gap_pct'], 0)} %). "
        f"Auch ohne Sondervermögen wächst der Rest von {fde(G.loc[2014, 'rest'])} auf {fde(G.loc[2025, 'rest'])} Mrd. € (2025).")
    k1, k2, k3 = st.columns(3)
    k1.metric("Abstand 2025", f"{fde(G.loc[2025, 'gap'])} Mrd. €", f"2014: {fde(G.loc[2014, 'gap'])} Mrd. €", delta_color="off")
    k2.metric("Anteil außerhalb Epl. 14, 2025", f"{fde(G.loc[2025, 'gap_pct'], 0)} %",
              f"{fde(G.loc[2025, 'gap_pct'] - G.loc[2014, 'gap_pct'], 0)} Pp. ggü. 2014")
    k3.metric("Rest ohne Sondervermögen, 2025", f"{fde(G.loc[2025, 'rest'])} Mrd. €",
              f"2014: {fde(G.loc[2014, 'rest'])} Mrd. €", delta_color="off")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Woraus die NATO-Meldung besteht, in Mrd. € (nominal)**")
        st.caption("Gestapelt: Einzelplan 14, Sondervermögen Bundeswehr und der Rest bis zur NATO-Meldung. "
                   "Die Zahl über dem Balken ist die NATO-Meldung.")
        fig = go.Figure()
        fig.add_bar(x=gp.jahr, y=gp.epl14_mrd, name="Einzelplan 14", marker_color=FARBEN["ausruestung"],
                    text=[fde(x) for x in gp.epl14_mrd], textposition="inside", hovertemplate="%{y:.1f} Mrd. €")
        fig.add_bar(x=gp.jahr, y=gp.sv_bw_mrd, name="Sondervermögen Bundeswehr", marker_color=FARBEN["sonstige"],
                    text=[fde(x) if x > 0 else "" for x in gp.sv_bw_mrd], textposition="inside", hovertemplate="%{y:.1f} Mrd. €")
        fig.add_bar(x=gp.jahr, y=gp.rest, name="Rest (andere Ressorts u. a.)", marker_color=GRAU,
                    text=[fde(x) for x in gp.rest], textposition="inside", hovertemplate="%{y:.1f} Mrd. €")
        fig.add_scatter(x=gp.jahr, y=gp.nato_mrd, mode="text", text=[fde(x) for x in gp.nato_mrd], textposition="top center",
                        name="NATO-Meldung", showlegend=False, textfont=dict(size=11, color="#222"), hovertemplate="NATO: %{y:.1f} Mrd. €")
        fig.update_layout(barmode="stack", uniformtext=dict(minsize=8, mode="hide"))
        st.plotly_chart(layout(fig, 460, "Mrd. €").update_yaxes(range=[0, gp.nato_mrd.max() * 1.12]), width="stretch")
        quellen(Q_NATO_T1, "[Wissenschaftliche Dienste des Bundestages: WD 4 - 30000 - 0023/26 (PDF)]"
                "(https://www.bundestag.de/resource/blob/1223168/WD-4-0003-0023-26_verteidigungsausgaben.pdf)",
                "Einzelplan 14 je Jahr: siehe Tabelle unten; der Rest ist eigene Berechnung (NATO minus Epl. 14 minus Sondervermögen).")
    with c2:
        st.markdown("**Anteil der NATO-Meldung außerhalb des Einzelplans 14, in %**")
        st.caption("Durchgezogen: alles außerhalb des Einzelplans 14. Gestrichelt: ohne das Sondervermögen, also nur der Rest.")
        fig = go.Figure()
        fig.add_scatter(x=gp.jahr, y=gp.gap_pct, name="Außerhalb Epl. 14", mode="lines+markers+text",
                        text=[fde(x, 0) for x in gp.gap_pct], textposition="top center",
                        line=dict(color=FARBEN["ausruestung"], width=3), hovertemplate="%{y:.1f} %")
        fig.add_scatter(x=gp.jahr, y=gp.rest_pct, name="Davon Rest ohne Sondervermögen", mode="lines+markers+text",
                        text=[fde(x, 0) for x in gp.rest_pct], textposition="bottom center",
                        line=dict(color=GRAU, width=2, dash="dash"), hovertemplate="%{y:.1f} %")
        st.plotly_chart(layout(fig, 460, "% der NATO-Meldung").update_yaxes(range=[0, gp.gap_pct.max() * 1.15]), width="stretch")
        quellen(Q_NATO_T1, "Eigene Berechnung aus NATO-Meldung, Einzelplan 14 und Sondervermögen.")
    with st.expander("Was steckt im Abstand und wie belastbar ist er?"):
        st.markdown(
            "- **Sondervermögen Bundeswehr:** Seit 2023 der größte Einzelposten außerhalb des Einzelplans 14.\n"
            "- **Rest:** Verteidigungsrelevante Ausgaben anderer Ressorts, etwa die Ukraine-Hilfe (Ertüchtigung im Einzelplan 60), "
            "Versorgungsleistungen oder Beiträge. Laut IW Köln entfielen 2024 rund 7,5 Mrd. € auf Ukraine-Hilfe und rund 7 Mrd. € auf "
            "„andere verteidigungsrelevante Ausgaben“, deren Herkunft nicht erkennbar ist. Die Bundesregierung schlüsselt den Rest "
            "nicht vollständig auf.\n"
            "- **Plausibilität:** Ein Fachartikel nennt Ausgaben außerhalb des Wehretats von 1,6 Mrd. € (2014) und rund 18,85 Mrd. € "
            "(2024). Die Werte hier liegen in derselben Größenordnung, sind aber nicht identisch abgegrenzt.\n"
            "- **Grenzen:** Die NATO-Werte für 2025 und 2026 sind Schätzungen. Beim Einzelplan 14 sind 2014–2019 und 2026 Soll-, "
            "2020–2025 Ist-Werte. Der Abstand ist deshalb eine Näherung, kein amtlicher Wert.\n\n"
            "Quellen: [IW Köln: Gerade so genug für die NATO? (April 2024)]"
            "(https://www.iwkoeln.de/studien/klaus-heiner-roehl-gerade-so-genug-fuer-die-nato.html), "
            "[cpm Defence Network](https://defence-network.com/trickst-bundesregierung-verteidigungsausgaben/)"
        )


    st.markdown("**Abstand je Jahr**")
    tg = gp[["jahr", "nato_mrd", "epl14_mrd", "epl14_pct", "sv_bw_mrd", "rest", "gap_pct"]].round(1)
    tg["jahr"] = tg.jahr.map(jahr_label)
    tg.columns = ["Jahr", "NATO-Meldung, Mrd. €", "Einzelplan 14, Mrd. €", "Einzelplan 14 in % der NATO-Meldung",
                  "Sondervermögen, Mrd. €", "Rest, Mrd. €", "Außerhalb Epl. 14, %"]
    st.dataframe(tg, hide_index=True, width="stretch")

    tb = bh[["jahr", "basis", "epl14_mrd", "sv_bw_mrd", "bund_mrd", "anteil_epl14", "anteil_mit_sv", "quelle"]].round(1)
    tb.columns = ["Jahr", "Basis", "Einzelplan 14, Mrd. €", "Sondervermögen, Mrd. €", "Bundeshaushalt, Mrd. €",
                  "Anteil Epl. 14, %", "Epl. 14 + SV im Verhältnis, %", "Quelle"]
    st.dataframe(tb, hide_index=True, width="stretch")

# ---------------------------------------------------------------- Abgleich SIPRI
with tabs[4]:
    st.subheader("SIPRI bestätigt die Größenordnung, verlegt den Sprung aber stärker in das Jahr 2025")
    ab = g[g.jahr <= 2025][["jahr", "nominal_eur", "anteil_bip", "real_aend", "real_eur"]].merge(
        s[["jahr", "lokal_eur", "anteil_bip_pct", "konstant_2024_usd"]], on="jahr")
    ab["sipri_real"] = S.konstant_2024_usd.pct_change().mul(100).reindex(ab.jahr).values
    ab["abw"] = (ab.lokal_eur / ab.nominal_eur - 1) * 100
    A = ab.set_index("jahr")
    summe = lambda col: A.loc[2023:2025, col].sum()
    na = g[["jahr", "nominal_eur", "anteil_bip", "real_aend"]]  # NATO inklusive Schätzung 2026
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ausgaben laut NATO und SIPRI, nominal in Mrd. €**")
        st.caption(f"Von 2014 bis 2024 liegt SIPRI unter der NATO, zuletzt bei {fde(A.loc[2024, 'abw'])} %. 2025 kehrt sich das um "
                   f"({fde(A.loc[2025, 'abw'])} %). Über 2023–2025 summiert beträgt der Abstand "
                   f"{fde((summe('lokal_eur') / summe('nominal_eur') - 1) * 100)} %. Für 2026 gibt es nur die NATO-Schätzung.")
        fig = go.Figure()
        fig.add_scatter(x=na.jahr, y=na.nominal_eur / 1e3, name="NATO", mode="lines+markers+text",
                        text=[fde(x / 1e3, 1) for x in na.nominal_eur], textposition="top center",
                        textfont=dict(size=10, color=FARBEN["ausruestung"]), line=dict(color=FARBEN["ausruestung"], width=2.5))
        fig.add_scatter(x=ab.jahr, y=ab.lokal_eur / 1e3, name="SIPRI", mode="lines+markers+text",
                        text=[fde(x / 1e3, 1) for x in ab.lokal_eur], textposition="bottom center",
                        textfont=dict(size=10, color=FARBEN["personal"]), line=dict(color=FARBEN["personal"], width=2.5))
        fig.update_traces(hovertemplate="%{y:.1f} Mrd. €")
        st.plotly_chart(layout(fig, 440, "Mrd. €").update_yaxes(range=[0, na.nominal_eur.max() / 1e3 * 1.15]), width="stretch")
        quellen(Q_NATO_T1, Q_SIPRI)
    with c2:
        st.markdown("**Reale Veränderung zum Vorjahr, in %**")
        st.caption(f"2025 meldet SIPRI {fde(A.loc[2025, 'sipri_real'])} % und die NATO-Schätzung {fde(A.loc[2025, 'real_aend'])} %. "
                   f"Für 2026 schätzt die NATO {fde(J.loc[2026, 'real_aend'])} %.")
        fig = go.Figure()
        fig.add_bar(x=na.jahr, y=na.real_aend, name="NATO", marker_color=FARBEN["ausruestung"], hovertemplate="%{y:.1f} %",
                    text=[fde(x, 1) for x in na.real_aend], textposition="outside", textfont=dict(size=9))
        fig.add_bar(x=ab.jahr, y=ab.sipri_real, name="SIPRI", marker_color=FARBEN["personal"], hovertemplate="%{y:.1f} %",
                    text=[fde(x, 1) for x in ab.sipri_real], textposition="outside", textfont=dict(size=9))
        fig.update_layout(uniformtext=dict(minsize=8, mode="show"))
        st.plotly_chart(layout(fig, 440, "%"), width="stretch")
        quellen(Q_NATO_T3, Q_SIPRI, "Die SIPRI-Veränderung ist aus den Werten in konstanten US-$ (Preise von 2024) berechnet.")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Anteil am BIP laut NATO und SIPRI**")
        st.caption(f"Die NATO erreicht 2024 genau {fde(ZIEL_ALT, 2)} %, SIPRI überschreitet die Marke erst 2025 und nennt "
                   f"für 2024 {fde(A.loc[2024, 'anteil_bip_pct'], 2)} %. 2026 schätzt die NATO {fde(J.loc[2026, 'anteil_bip'], 2)} %.")
        fig = go.Figure()
        fig.add_scatter(x=na.jahr, y=na.anteil_bip, name="NATO", mode="lines+markers+text",
                        text=[fde(x, 2) for x in na.anteil_bip], textposition="top center",
                        textfont=dict(size=10, color=FARBEN["ausruestung"]), line=dict(color=FARBEN["ausruestung"], width=2.5))
        fig.add_scatter(x=ab.jahr, y=ab.anteil_bip_pct, name="SIPRI", mode="lines+markers+text",
                        text=[fde(x, 2) for x in ab.anteil_bip_pct], textposition="bottom center",
                        textfont=dict(size=10, color=FARBEN["personal"]), line=dict(color=FARBEN["personal"], width=2.5))
        fig.add_hline(y=ZIEL_ALT, line_dash="dot", line_color="#777")
        fig.update_traces(hovertemplate="%{y:.2f} %")
        st.plotly_chart(layout(fig, 440, "% des BIP").update_yaxes(range=[0.8, na.anteil_bip.max() * 1.15]), width="stretch")
        quellen(Q_NATO_T3, Q_SIPRI)
    with c4:
        st.markdown("**Warum der reale Anstieg 2014–2025 abweicht**")
        nomN, nomS = A.loc[2025, "nominal_eur"] / A.loc[2014, "nominal_eur"], A.loc[2025, "lokal_eur"] / A.loc[2014, "lokal_eur"]
        realN, realS = A.loc[2025, "real_eur"] / A.loc[2014, "real_eur"], A.loc[2025, "konstant_2024_usd"] / A.loc[2014, "konstant_2024_usd"]
        st.table(pd.DataFrame({"NATO": [fde(nomN, 2), fde(nomN / realN, 2), fde(realN, 2)],
                               "SIPRI": [fde(nomS, 2), fde(nomS / realS, 2), fde(realS, 2)]},
                              index=["Nominal", "Preiseffekt, implizit", "Real"]).rename_axis("Faktor 2014–2025"))
        gaps = (aa.sipri_2025 - aa.nato_2025).abs()
        de_gap = float((aa.sipri_2025 - aa.nato_2025)[aa.land == "Deutschland"].iloc[0])
        st.caption("SIPRI wächst stärker: Die Ausgaben starten niedriger, enden 2025 höher, und die Preisbereinigung fällt "
                   f"geringer aus. Deutschland weicht beim BIP-Anteil 2025 nur um {fde(de_gap, 2)} Prozentpunkte ab, der Median "
                   f"aller Länder liegt bei {fde(gaps.median(), 2)}. Beide Quellen haben eigene Abgrenzungen und Preisbasen "
                   "(NATO: 2021, SIPRI: 2024); reale Werte werden deshalb nur über Faktoren verglichen. "
                   "Der Vergleich endet 2025, weil SIPRI für 2026 noch keine Daten hat.")
        quellen(Q_NATO_T1, Q_NATO_T3, Q_SIPRI, "Die Faktoren sind eigene Berechnungen aus beiden Datensätzen.")
    st.markdown("**Abweichung SIPRI minus NATO beim BIP-Anteil 2025, in Prozentpunkten**")
    st.caption("Bei großen Abweichungen wie Luxemburg oder Litauen sollte man vor dem Zitieren die Quellenangaben prüfen. "
               "Die NATO-Werte für 2025 sind Schätzungen; für 2026 ist kein Vergleich möglich, weil SIPRI noch keine Daten hat.")
    d = aa.assign(diff=aa.sipri_2025 - aa.nato_2025).sort_values("diff")
    fig = go.Figure(go.Bar(
        y=d.land, x=d["diff"], orientation="h", text=[fde(x, 2) for x in d["diff"]], textposition="outside",
        marker_color=[FARBEN["ausruestung"] if l == "Deutschland" else GRAU for l in d.land],
        customdata=d[["nato_2025", "sipri_2025"]],
        hovertemplate="%{y}<br>NATO: %{customdata[0]:.2f} %<br>SIPRI: %{customdata[1]:.2f} %<extra></extra>"))
    fig.update_layout(height=760, margin=dict(l=10, r=40, t=10, b=10), separators=",.")
    st.plotly_chart(fig, width="stretch")
    quellen(Q_NATO_T3, Q_SIPRI)

# ---------------------------------------------------------------- Langfristvergleich
with tabs[5]:
    st.subheader("Im Langfristvergleich: real auf Rekordniveau, beim BIP-Anteil noch unter dem Kalten Krieg")
    kw = s[s.jahr <= 1990]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Reale Militärausgaben 1953–2025, in Mrd. US-$ (Preise von 2024)**")
        st.caption(f"2025 liegen die Ausgaben mit {fde(S.loc[2025, 'konstant_2024_usd'] / 1e3)} Mrd. US-$ "
                   f"{fde((S.loc[2025, 'konstant_2024_usd'] / S.loc[1990, 'konstant_2024_usd'] - 1) * 100, 0)} % über dem "
                   f"bisherigen Höchstwert von 1990 ({fde(S.loc[1990, 'konstant_2024_usd'] / 1e3)} Mrd. US-$). Bis 2006 waren sie "
                   f"um {fde((1 - S.loc[2006, 'konstant_2024_usd'] / S.loc[1990, 'konstant_2024_usd']) * 100, 0)} % gefallen.")
        fig = go.Figure(go.Scatter(x=s.jahr, y=s.konstant_2024_usd / 1e3, line=dict(color=FARBEN["ausruestung"], width=2.5),
                                   hovertemplate="%{x}: %{y:.1f} Mrd. US-$<extra></extra>"))
        fig.add_vline(x=1990, line_dash="dash", line_color="#777", annotation_text="1990")
        st.plotly_chart(layout(fig, y_titel="Mrd. US-$", schaetzung=False), width="stretch")
    with c2:
        st.markdown("**Militärausgaben in % des BIP, 1953–2025**")
        st.caption(f"2025 sind es {fde(S.loc[2025, 'anteil_bip_pct'], 2)} %. Im Durchschnitt 1953–1990 waren es "
                   f"{fde(kw.anteil_bip_pct.mean(), 2)} %, der Höchstwert lag {int(S.anteil_bip_pct.idxmax())} bei "
                   f"{fde(S.anteil_bip_pct.max(), 2)} %, der Tiefstwert {int(S.anteil_bip_pct.idxmin())} bei "
                   f"{fde(S.anteil_bip_pct.min(), 2)} %.")
        fig = go.Figure(go.Scatter(x=s.jahr, y=s.anteil_bip_pct, line=dict(color=FARBEN["ausruestung"], width=2.5),
                                   hovertemplate="%{x}: %{y:.2f} %<extra></extra>"))
        fig.add_vline(x=1990, line_dash="dash", line_color="#777", annotation_text="1990")
        fig.add_hline(y=ZIEL_KERN, line_dash="dash", line_color="#777", annotation_text=f"Hague-Ziel: {fde(ZIEL_KERN)} %",
                      annotation_position="bottom right")
        fig.add_hline(y=ZIEL_ALT, line_dash="dot", line_color="#777")
        st.plotly_chart(layout(fig, y_titel="% des BIP", schaetzung=False), width="stretch")
    st.markdown("**Militärausgaben in % der gesamten Staatsausgaben, 1991–2025**")
    sg = s.dropna(subset=["anteil_staat_pct"])
    SG = sg.set_index("jahr").anteil_staat_pct
    st.caption(f"2025 sind es {fde(SG.loc[2025], 2)} %, nach {fde(SG.loc[2014], 2)} % in 2014 und dem Tiefstwert von "
               f"{fde(SG.min(), 2)} % in {int(SG.idxmin())}. Damit liegt der Anteil wieder über dem Wert von 1991 "
               f"({fde(SG.loc[1991], 2)} %), dem ersten Jahr der Reihe.")
    fig = go.Figure()
    fig.add_scatter(x=sg.jahr, y=sg.anteil_staat_pct, name="Anteil an den Staatsausgaben",
                    line=dict(color=FARBEN["ausruestung"], width=3), hovertemplate="%{y:.2f} %")
    fig.add_scatter(x=sg.jahr, y=sg.anteil_bip_pct, name="Anteil am BIP (zum Vergleich)",
                    line=dict(color=GRAU, width=2), hovertemplate="%{y:.2f} %")
    st.plotly_chart(layout(fig, 400, "%", schaetzung=False), width="stretch")
    with st.expander("Was zählt zu den Staatsausgaben?"):
        st.markdown(
            "- **Staatsausgaben:** Die Ausgaben des Gesamtstaats laut IWF (World Economic Outlook), also von Bund, Ländern "
            "und Gemeinden. Es ist **nicht** der Bundeshaushalt allein.\n"
            "- **Militärausgaben:** In der Abgrenzung von SIPRI, nicht der NATO. Die Werte passen deshalb zur SIPRI-Reihe "
            "auf diesem Reiter, nicht direkt zu den NATO-Zahlen der anderen Reiter.\n"
            "- **Zeitraum:** Für Deutschland weist SIPRI den Anteil erst ab 1991 aus.\n\n"
            "Der Anteil am Bundeshaushalt wäre deutlich höher, weil Verteidigung fast nur vom Bund finanziert wird, "
            "die Staatsausgaben aber auch Länder und Gemeinden umfassen."
        )

    st.info("SIPRI führt die DDR gesondert. Die Werte vor 1990 stehen deshalb vermutlich für Westdeutschland; das ist eine "
            "Lesart, keine ausdrückliche Angabe im Datensatz.")

# ---------------------------------------------------------------- Einordnung
with tabs[6]:
    st.subheader("Was das für die Frage nach der Dauerhaftigkeit heißt")
    st.markdown(
        "- **Für strukturellen Wandel spricht:** Der Anstieg betrifft nicht nur das Niveau, sondern auch die Zusammensetzung, "
        "denn der Ausrüstungsanteil hat sich mehr als verdoppelt. Das Hague-Ziel würde weiteres Wachstum bedeuten.\n"
        "- **Für Vorsicht spricht:** Der Großteil des Anstiegs ist nur wenige Jahre alt, und die Werte für 2025 und 2026 sind "
        "Schätzungen. Ob sie Bestand haben, lässt sich aus diesen Tabellen noch nicht ablesen.\n"
        "- **Historische Einordnung:** Real liegen die Ausgaben laut SIPRI über dem Niveau des Kalten Kriegs, gemessen am BIP "
        "aber noch darunter. Die Zeit nach 1990 zeigt, dass ein hohes Niveau nicht von selbst bestehen bleibt: Real fielen "
        "die Ausgaben danach über Jahre.\n"
        "- **Spielraum bei den Meldedaten:** Regelwidriges Hineinrechnen, etwa in „Sonstiges“, lässt sich aus diesen Daten nicht "
        "belegen. Es gibt aber Spielraum, denn die Länder melden ihre Ausgaben selbst, eine unabhängige Prüfung fehlt laut einem "
        "Fachbeitrag, und Deutschland legt die Zusammensetzung nicht vollständig offen. Zur deutschen Quote zählen auch Mittel "
        "außerhalb des Verteidigungshaushalts, etwa die Ukraine-Hilfe.\n"
        "- **Zur Messgröße:** Der BIP-Anteil hängt auch vom BIP ab und sagt wenig über die Industrie. Für die Staatsnachfrage "
        "ist die reale Ausrüstungssumme aussagekräftiger.\n"
        "- **Grenze der Daten:** Ausrüstungsausgaben sind nicht gleich Umsatz der deutschen Industrie, denn die Tabellen zeigen "
        "weder Importanteile noch Zulieferer oder Exporte. Dafür braucht ihr weitere Quellen."
    )

# ---------------------------------------------------------------- Daten & Quellen
with tabs[7]:
    st.subheader("Alle Werte für Deutschland")
    tab = g[["jahr", "nominal_eur", "real_eur", "real_usd", "anteil_bip", "real_aend", "pro_kopf_usd", "personal_tsd",
             "ausruestung", "personal", "infrastruktur", "sonstige"]].copy()
    tab["jahr"] = tab.jahr.map(jahr_label)
    tab.columns = ["Jahr", "Nominal, Mio. €", "Real, Mio. €", "Real, Mio. US-$", "% des BIP", "Real ggü. Vorjahr, %",
                   "Pro Kopf, US-$", "Personal, Tsd.", "Ausrüstung, %", "Personal, %", "Infrastruktur, %", "Sonstiges, %"]
    st.dataframe(tab, hide_index=True, width="stretch")
    st.download_button("NATO-Werte Deutschland als CSV", g.to_csv(index=False).encode("utf-8"), "nato_deutschland.csv", "text/csv")

    st.subheader("Jahresvergleich NATO und SIPRI")
    vg = ab[["jahr", "nominal_eur", "lokal_eur", "abw", "anteil_bip", "anteil_bip_pct", "real_aend", "sipri_real"]].round(2)
    vg.columns = ["Jahr", "NATO, Mio. €", "SIPRI, Mio. €", "Abweichung, %", "NATO, % BIP", "SIPRI, % BIP",
                  "NATO, real %", "SIPRI, real %"]
    st.dataframe(vg, hide_index=True, width="stretch")
    st.download_button("SIPRI-Werte Deutschland als CSV", s.to_csv(index=False).encode("utf-8"), "sipri_deutschland.csv", "text/csv")

    st.subheader("Quellen")
    st.markdown(
        "- [NATO: Defence Expenditure of NATO Countries, Bericht 2026 (PDF)](https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2026-en.pdf). "
        "Tabellen 1–8 und Definition der Kernausgaben; Werte für 2025 und 2026 sind Schätzungen.\n"
        "- [SIPRI: Military Expenditure Database](https://sipri.org/databases/milex). Datenstand April 2026.\n"
        "- [SIPRI: Datensatz 1949–2025, Version 1.2 (Excel)](https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2025_v1.2.xlsx). "
        "Grundlage für den Abgleich und die Langfristreihe.\n"
        "- [SIPRI: Sources and methods](https://www.sipri.org/databases/milex/sources-and-methods). Definition und Preisbereinigung.\n"
        "- [Wissenschaftliche Dienste des Bundestages: Entwicklung der Verteidigungsausgaben des Bundes, WD 4 - 30000 - 0023/26 (PDF)](https://www.bundestag.de/resource/blob/1223168/WD-4-0003-0023-26_verteidigungsausgaben.pdf). "
        "Einzelplan 14 und Sondervermögen, Soll und Ist 2020–2026.\n"
        "- [Bundestag: Bundeshaushalt im Vergleich, Ist-Ausgaben 2010–2024 (PDF)](https://www.bundestag.de/resource/blob/272958/bf3d27099d658b6df3b22fe2633f0b58/Kapitel_17_01_Bundeshaushalt_und_Haushalt_des_Bundestages__Einzelplan_02__im_Vergleich-pdf.pdf).\n"
        "- [BMF: Jahresabschluss Bundeshaushalt 2025 (PDF)](https://table.media/assets/berlin/26-02-11_jahresabschluss_bundeshaushalt_2025.pdf). Ist-Ausgaben 2025.\n"
        "- [ESUT: Haushaltsgesetz 2026 tritt zum 1. Januar in Kraft](https://esut.de/en/2025/12/meldungen/66604/haushaltsgesetz-2026-tritt-zum-1-januar-in-kraft/). Bundeshaushalt und Einzelplan 14 2026.\n"
        "- [bpb: Der Verteidigungshaushalt (2017)](https://www.bpb.de/themen/militaer/deutsche-verteidigungspolitik/249290/der-verteidigungshaushalt-trendwende-bei-den-verteidigungsausgaben/). Soll 2016 und 2017.\n"
        "- [vergabeblog: Bundeshaushalt 2019](https://vergabeblog.de/2018-11-09/bundeshaushalt-2019-im-haushaltsausschuss-beschlossen/), "
        "[Haushalt 2014](https://vergabeblog.de/2014-06-06/bund-2965-milliarden-euro-ausgaben-eingeplant/), "
        "[Bundestag: Haushalt 2015](https://www.bundestag.de/webarchiv/textarchiv/2014/kw46_pa_haushalt-340794). Soll-Werte 2014–2019.\n"
        "- [Global Policy: Spend First, Define Later (PDF)](https://www.globalpolicyjournal.com/sites/default/files/pdf/Spend%20First%2C%20Define%20Later%2C%20NATO%E2%80%99s%20Accountability%20Gap.pdf). "
        "Selbstmeldung und fehlende unabhängige Prüfung; Einschätzung der Autorin.\n"
        "- [IW Köln: Gerade so genug für die NATO? (April 2024)](https://www.iwkoeln.de/studien/klaus-heiner-roehl-gerade-so-genug-fuer-die-nato.html). "
        "Zusammensetzung der deutschen Quote 2024, inklusive Ukraine-Hilfe.\n"
        "- [cpm Defence Network: Trickst die Bundesregierung durch erfundene Verteidigungsausgaben?](https://defence-network.com/trickst-bundesregierung-verteidigungsausgaben/) "
        "Kritischer Artikel zu fehlender Offenlegung; einseitige Perspektive."
    )
    st.caption("Reale Werte in Preisen und Wechselkursen von 2021 (NATO) bzw. 2024 (SIPRI). Reale Kategorienwerte, Indizes, "
               "Faktoren und die Lücke zum Hague-Ziel sind eigene Berechnungen. Für den NATO-Richtwert von 20 % bei der "
               "Ausrüstung und die Bezeichnung „Bisheriges Ziel“ für die 2-%-Linie ist hier noch keine Quelle verlinkt.")
