import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta


def berechne_zinsen_mit_monatlicher_gutschrift(
    laufzeit_in_monaten, sparsumme, jahreszins, startdatum=None
):
    if startdatum is None:
        startdatum = datetime.date.today()
    else:
        startdatum = datetime.datetime.strptime(startdatum, "%Y-%m-%d").date()

    tageszinssatz = jahreszins / 365

    daten = []
    aktuelles_datum = startdatum
    enddatum = startdatum + relativedelta(months=laufzeit_in_monaten)
    aktueller_kontostand = sparsumme
    gesamt_zinsen = 0.0
    monatliche_zinsen = 0.0
    letzter_monat = aktuelles_datum.month

    while aktuelles_datum < enddatum:
        tageszins = aktueller_kontostand * tageszinssatz
        gesamt_zinsen += tageszins
        monatliche_zinsen += tageszins

        # Überprüfung, ob ein Monatsende erreicht wurde
        if (
            aktuelles_datum + datetime.timedelta(days=1)
        ).month != aktuelles_datum.month:
            # Zinsgutschrift am Monatsende
            aktueller_kontostand += monatliche_zinsen
            monatliche_zinsen = 0.0  # Monatliche Zinsen zurücksetzen

        daten.append(
            {
                "Datum": aktuelles_datum,
                "Tageszins": tageszins,
                "Gesamtzinsen": gesamt_zinsen,
                "Kontostand": aktueller_kontostand,
            }
        )
        aktuelles_datum += datetime.timedelta(days=1)

    df = pd.DataFrame(daten)
    df["Datum"] = pd.to_datetime(df["Datum"])
    return df


# Streamlit-App
st.title("Zinsberechnung mit monatlicher Zinsgutschrift")

st.sidebar.header("Eingabedaten")

# Eingabefelder
sparsumme = st.sidebar.number_input(
    "Sparsumme (€)", min_value=0.0, value=10000.0, step=1000.0
)
laufzeit_in_monaten = st.sidebar.number_input(
    "Laufzeit (Monate)", min_value=1, value=12, step=1
)
jahreszins_prozent = st.sidebar.number_input(
    "Jahreszinssatz (% p.a.)", min_value=0.0, value=3.75, step=0.01
)
startdatum = st.sidebar.date_input("Startdatum", datetime.date.today())

# Umwandlung des Jahreszinssatzes in Dezimalform
jahreszins = jahreszins_prozent / 100

# Berechnung durchführen
df_zinsen = berechne_zinsen_mit_monatlicher_gutschrift(
    laufzeit_in_monaten, sparsumme, jahreszins, startdatum.strftime("%Y-%m-%d")
)

# Beschreibung der Berechnung
st.header("Beschreibung der Berechnung")
st.markdown(
    """
Die Zinsen werden nach dem Prinzip der täglichen Zinsberechnung mit monatlicher Zinsgutschrift ermittelt:

- **Tageszinssatz**: Der jährliche Zinssatz wird durch 365 geteilt, um den täglichen Zinssatz zu erhalten.
"""
)
st.latex(
    r"""
\text{Tageszinssatz} = \frac{\text{Jahreszinssatz}}{365} = \frac{%.2f\%%}{365} \approx %.6f\%% \text{ pro Tag}
"""
    % (jahreszins_prozent, jahreszins_prozent / 365)
)
st.markdown(
    """
- **Tägliche Zinsberechnung**: Für jeden Tag wird der Tageszins berechnet:
"""
)
st.latex(
    r"""
\text{Tageszins} = \text{Aktueller Kontostand} \times \text{Tageszinssatz}
"""
)
st.markdown(
    """
- **Monatliche Zinsgutschrift**: Am Ende jedes Monats werden die gesammelten Zinsen dem Kontostand hinzugefügt.

- **Laufzeit**: Die tatsächliche Anzahl der Tage wird basierend auf dem Startdatum und der Laufzeit in Monaten berechnet.
"""
)

# Ergebnisse anzeigen
st.header("Ergebnisse")

# Gesamtzinsen
gesamtzinsen = df_zinsen["Gesamtzinsen"].iloc[-1]
st.subheader(f"Gesamtzinsen über {laufzeit_in_monaten} Monate: {gesamtzinsen:.2f} €")

# Anzahl der Tage
anzahl_tage = len(df_zinsen)
st.write(f"Anzahl der Tage: {anzahl_tage}")

# Diagramm erstellen - Kontostandentwicklung
st.subheader("Kontostandentwicklung über die Zeit")
fig = px.line(
    df_zinsen,
    x="Datum",
    y="Kontostand",
    title="Entwicklung des Kontostands über die Zeit",
)
st.plotly_chart(fig)

# Zusätzliche Metriken
st.subheader("Zusätzliche Informationen")
durchschnittlicher_tageszins = df_zinsen["Tageszins"].mean()
st.write(f"Durchschnittlicher Tageszins: {durchschnittlicher_tageszins:.2f} €")

# Option zur Anzeige der Zinstabelle mit Diagrammen
anzeige_option = st.selectbox(
    "Zinstabelle anzeigen als:", ("Keine", "Täglich", "Monatlich")
)

if anzeige_option == "Täglich":
    st.subheader("Detaillierte Zinstabelle (Täglich)")
    st.dataframe(df_zinsen)
    # Diagramme hinzufügen
    st.subheader("Tägliche Zinsen")
    fig2 = px.bar(df_zinsen, x="Datum", y="Tageszins", title="Tägliche Zinsen")
    st.plotly_chart(fig2)

    # Kontostandentwicklung täglich
    st.subheader("Kontostandentwicklung (Täglich)")
    fig4 = px.line(
        df_zinsen, x="Datum", y="Kontostand", title="Kontostand über die Zeit (Täglich)"
    )
    st.plotly_chart(fig4)

elif anzeige_option == "Monatlich":
    st.subheader("Detaillierte Zinstabelle (Monatlich)")
    # Monatliche Zusammenfassung
    df_zinsen["Monat"] = df_zinsen["Datum"].dt.to_period("M")
    df_monatlich = (
        df_zinsen.groupby("Monat")
        .agg({"Tageszins": "sum", "Gesamtzinsen": "last", "Kontostand": "last"})
        .reset_index()
    )
    # Konvertiere 'Monat' zurück zu Datum für bessere Lesbarkeit
    df_monatlich["Monat"] = df_monatlich["Monat"].dt.to_timestamp()
    st.dataframe(df_monatlich)

    # Diagramme hinzufügen
    st.subheader("Monatliche Zinsen")
    fig3 = px.bar(df_monatlich, x="Monat", y="Tageszins", title="Monatliche Zinsen")
    st.plotly_chart(fig3)

    # Kontostandentwicklung monatlich
    st.subheader("Kontostandentwicklung (Monatlich)")
    fig5 = px.line(
        df_monatlich, x="Monat", y="Kontostand", title="Kontostand über die Monate"
    )
    st.plotly_chart(fig5)
