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


@st.cache_data
def lade_daten():
    g = pd.read_csv(DATA / "germany.csv")
    v = pd.read_csv(DATA / "vergleich.csv")
    a = pd.read_csv(DATA / "allies.csv")
    t = pd.read_csv(DATA / "bip_trend.csv")
    s = pd.read_csv(DATA / "sipri_de.csv").dropna(subset=["anteil_bip_pct"])
    aa = pd.read_csv(DATA / "abgleich_alliierte.csv")
    for k in KATEGORIEN:
        g[f"{k}_real"] = g["real_eur"] * g[k] / 1e5  # Mrd. €, Preise 2021
    return g, v, a, t, s, aa


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


g, v, a, t, s, aa = lade_daten()
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

tabs = st.tabs(["Entwicklung", "BIP-Anteil", "Kategorien & Personal", "Abgleich SIPRI",
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

# ---------------------------------------------------------------- Abgleich SIPRI
with tabs[3]:
    st.subheader("SIPRI bestätigt die Größenordnung, verlegt den Sprung aber stärker in das Jahr 2025")
    ab = g[g.jahr <= 2025][["jahr", "nominal_eur", "anteil_bip", "real_aend", "real_eur"]].merge(
        s[["jahr", "lokal_eur", "anteil_bip_pct", "konstant_2024_usd"]], on="jahr")
    ab["sipri_real"] = S.konstant_2024_usd.pct_change().mul(100).reindex(ab.jahr).values
    ab["abw"] = (ab.lokal_eur / ab.nominal_eur - 1) * 100
    A = ab.set_index("jahr")
    summe = lambda col: A.loc[2023:2025, col].sum()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ausgaben laut NATO und SIPRI, nominal in Mrd. €**")
        st.caption(f"Von 2014 bis 2024 liegt SIPRI unter der NATO, zuletzt bei {fde(A.loc[2024, 'abw'])} %. 2025 kehrt sich das um "
                   f"({fde(A.loc[2025, 'abw'])} %). Über 2023–2025 summiert beträgt der Abstand "
                   f"{fde((summe('lokal_eur') / summe('nominal_eur') - 1) * 100)} %.")
        fig = go.Figure()
        fig.add_scatter(x=ab.jahr, y=ab.nominal_eur / 1e3, name="NATO", line=dict(color=FARBEN["ausruestung"], width=2.5))
        fig.add_scatter(x=ab.jahr, y=ab.lokal_eur / 1e3, name="SIPRI", line=dict(color=FARBEN["personal"], width=2.5))
        fig.update_traces(hovertemplate="%{y:.1f} Mrd. €")
        st.plotly_chart(layout(fig, y_titel="Mrd. €", schaetzung=False).update_xaxes(dtick=2), width="stretch")
    with c2:
        st.markdown("**Reale Veränderung zum Vorjahr, in %**")
        st.caption(f"2025 meldet SIPRI {fde(A.loc[2025, 'sipri_real'])} % und die NATO-Schätzung {fde(A.loc[2025, 'real_aend'])} %.")
        fig = go.Figure()
        fig.add_bar(x=ab.jahr, y=ab.real_aend, name="NATO", marker_color=FARBEN["ausruestung"], hovertemplate="%{y:.1f} %")
        fig.add_bar(x=ab.jahr, y=ab.sipri_real, name="SIPRI", marker_color=FARBEN["personal"], hovertemplate="%{y:.1f} %")
        st.plotly_chart(layout(fig, y_titel="%", schaetzung=False).update_xaxes(dtick=2), width="stretch")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Anteil am BIP laut NATO und SIPRI**")
        st.caption(f"Die NATO erreicht 2024 genau {fde(ZIEL_ALT, 2)} %, SIPRI überschreitet die Marke erst 2025 und nennt "
                   f"für 2024 {fde(A.loc[2024, 'anteil_bip_pct'], 2)} %.")
        fig = go.Figure()
        fig.add_scatter(x=ab.jahr, y=ab.anteil_bip, name="NATO", line=dict(color=FARBEN["ausruestung"], width=2.5))
        fig.add_scatter(x=ab.jahr, y=ab.anteil_bip_pct, name="SIPRI", line=dict(color=FARBEN["personal"], width=2.5))
        fig.add_hline(y=ZIEL_ALT, line_dash="dot", line_color="#777")
        fig.update_traces(hovertemplate="%{y:.2f} %")
        st.plotly_chart(layout(fig, y_titel="% des BIP", schaetzung=False).update_xaxes(dtick=2), width="stretch")
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
                   "(NATO: 2021, SIPRI: 2024); reale Werte werden deshalb nur über Faktoren verglichen.")
    st.markdown("**Abweichung SIPRI minus NATO beim BIP-Anteil 2025, in Prozentpunkten**")
    st.caption("Bei großen Abweichungen wie Luxemburg oder Litauen sollte man vor dem Zitieren die Quellenangaben prüfen. "
               "Die NATO-Werte für 2025 sind Schätzungen.")
    d = aa.assign(diff=aa.sipri_2025 - aa.nato_2025).sort_values("diff")
    fig = go.Figure(go.Bar(
        y=d.land, x=d["diff"], orientation="h", text=[fde(x, 2) for x in d["diff"]], textposition="outside",
        marker_color=[FARBEN["ausruestung"] if l == "Deutschland" else GRAU for l in d.land],
        customdata=d[["nato_2025", "sipri_2025"]],
        hovertemplate="%{y}<br>NATO: %{customdata[0]:.2f} %<br>SIPRI: %{customdata[1]:.2f} %<extra></extra>"))
    fig.update_layout(height=760, margin=dict(l=10, r=40, t=10, b=10), separators=",.")
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- Langfristvergleich
with tabs[4]:
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
with tabs[5]:
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
with tabs[6]:
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
