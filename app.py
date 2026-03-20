

# TP1 de LY Néné Gallé étudiante M1-ECAP Nantes Université
# Création d'un dashboard de vente pour une boutique fictive "ECAP Boutique"
# Professeur : Mr Abdoul Razac Sane
# librairies utilisées : pandas, plotly, dash, dash_bootstrap_components

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc


#J'importe le  Jeu de données
df = pd.read_csv("data.csv")

# colonnes que j'ai utilisées pour le dashboard (je les filtre pour éviter les erreurs si jamais une colonne est manquante)
cols_utiles = [
    "CustomerID", "Gender", "Location", "Product_Category",
    "Quantity", "Avg_Price", "Transaction_Date", "Month", "Discount_pct"
]
cols_utiles = [c for c in cols_utiles if c in df.columns]
df = df[cols_utiles].copy()

# Client
if "CustomerID" in df.columns:
    df["CustomerID"] = df["CustomerID"].fillna(0).astype(int)

# dates
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")
df = df.dropna(subset=["Transaction_Date"]).copy()

# mois
if "Month" not in df.columns:
    df["Month"] = df["Transaction_Date"].dt.month
df["Month"] = df["Month"].astype(int)

# chiffre d'affaire ligne
df["Total_price"] = df["Quantity"] * df["Avg_Price"] * (1 - df["Discount_pct"] / 100)
df["Chiffre_affaire"] = df["Total_price"]

# semaine
df["Week"] = df["Transaction_Date"].dt.to_period("W").dt.start_time

# liste des zones
locations = sorted(df["Location"].dropna().unique().tolist())



# COULEURS ET STYLES

BLEU_NUIT = "#0B1F3A"
BLEU_NUIT_CLAIR = "#12345A"
BLANC = "white"

style_titre_section = {
    "backgroundColor": BLEU_NUIT,
    "color": BLANC,
    "borderRadius": "999px",
    "padding": "10px 25px",
    "display": "inline-block",
    "fontWeight": "bold",
    "fontSize": "18px",
    "marginBottom": "15px",
    "boxShadow": "0 4px 10px rgba(0,0,0,0.20)"
}
# je définis les tyle pour les cartes KPI
style_carte_kpi = {
    "background": "linear-gradient(135deg, #0B1F3A, #12345A)",
    "border": "none",
    "borderRadius": "60px",
    "boxShadow": "0 6px 14px rgba(0,0,0,0.25)",
    "padding": "10px"
}


# ici je définis les fonctions de calculs et graphiques comme vu en cours 
def frequence_meilleure_vente(data, top=10, ascending=False):
    result = (
        data.groupby("Product_Category")["Quantity"]
        .sum()
        .sort_values(ascending=ascending)
        .head(top)
    )
    return result


def chiffre_affaire(data):
    CA = (data["Quantity"] * data["Avg_Price"] * (1 - data["Discount_pct"] / 100)).sum()
    return CA


def ca_par_mois(data, mois):
    d = data[data["Month"] == mois]
    CA = (d["Quantity"] * d["Avg_Price"] * (1 - d["Discount_pct"] / 100)).sum()
    return CA


def indicateur_du_mois(data, mois):
    d = data[data["Month"] == mois]
    CA = (d["Quantity"] * d["Avg_Price"] * (1 - d["Discount_pct"] / 100)).sum()
    return CA


def barplot_top10_ventes(data, top=10, ascending=False):
    totals = (
        data.groupby("Product_Category")["Quantity"]
        .sum()
        .sort_values(ascending=ascending)
        .head(top)
    )

    tmp = (
        data[data["Product_Category"].isin(totals.index)]
        .groupby(["Product_Category", "Gender"])["Quantity"]
        .sum()
        .reset_index()
        if "Gender" in data.columns
        else data[data["Product_Category"].isin(totals.index)]
             .groupby(["Product_Category"])["Quantity"]
             .sum()
             .reset_index()
    )

    order = list(totals.index)

    if "Gender" in tmp.columns:
        fig = px.bar(
            tmp,
            x="Quantity",
            y="Product_Category",
            color="Gender",
            color_discrete_map={"M": "blue", "F": "pink"},
            orientation="h",
            barmode="group",
            category_orders={"Product_Category": order},
            labels={"Quantity": "Total ventes", "Product_Category": ""}
        )
    else:
        fig = px.bar(
            tmp,
            x="Quantity",
            y="Product_Category",
            orientation="h",
            category_orders={"Product_Category": order},
            labels={"Quantity": "Total ventes", "Product_Category": ""}
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig


def plot_evolution_chiffre_affaire(data):
    if "Week" in data.columns:
        evolution = (
            data.groupby("Week")["Chiffre_affaire"]
            .sum()
            .reset_index()
            .sort_values("Week")
        )
        fig = px.line(
            evolution,
            x="Week",
            y="Chiffre_affaire",
            labels={"Week": "Semaine", "Chiffre_affaire": "Chiffre d’affaire"}
        )
    else:
        evolution = (
            data.groupby("Month")["Chiffre_affaire"]
            .sum()
            .reset_index()
            .sort_values("Month")
        )
        fig = px.line(
            evolution,
            x="Month",
            y="Chiffre_affaire",
            labels={"Month": "Mois", "Chiffre_affaire": "Chiffre d’affaire"}
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig


def plot_chiffre_affaire_mois(data):
    ca_mois_ = (
        data.groupby("Month")["Chiffre_affaire"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    fig = px.bar(
        ca_mois_,
        x="Month",
        y="Chiffre_affaire",
        labels={"Month": "Mois", "Chiffre_affaire": "Chiffre d’affaire"}
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig


def plot_ventes_mois(data):
    ventes_mois = (
        data.groupby("Month")["Quantity"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    fig = px.bar(
        ventes_mois,
        x="Month",
        y="Quantity",
        labels={"Month": "Mois", "Quantity": "Total ventes"}
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig


# conception du dashboard interactif
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # pour le déploiement sur Render 
app.title = "ECAP Boutique"

app.layout = dbc.Container([

    # ligne titre + filtre
    # ici on utilise 2 colonnes : une pour le titre et une pour le dropdown de sélection de la zone
    # J'ai ajouté un style pour le titre pour le rendre plus visible et moderne, et j'ai mis un style simple pour le dropdown
    dbc.Row([
        dbc.Col(
            html.H1(
    "ECAP Boutique",
    style={
        "fontWeight": "bold",
        "fontSize": "42px",  
        "color": "#87CEEB",  
        "fontFamily": "Segoe UI, Arial, sans-serif",  
        "letterSpacing": "2px",
        "textTransform": "uppercase",
        "textShadow": "2px 2px 8px rgba(0,0,0,0.4)",  
        "marginTop": "10px"
    }
), md=8),
         # colonne du dropdown pour choisir la zone
        dbc.Col([
            html.Label("Choisissez une zone", style={"color": "white", "fontWeight": "bold"}),
            dcc.Dropdown(
                id="zone",
                options=[{"label": "All", "value": "All"}] + [{"label": x, "value": x} for x in locations],
                value="All",
                clearable=False
            )
        ], md=4)
    ], className="mb-4"),

    dbc.Row([

        # Partie gauche pour les KPI et le top 10
        dbc.Col([

            # cartes KPI
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("Décembre", style={
                                "color": "white",
                                "textAlign": "center",
                                "marginBottom": "5px"
                            }),
                            html.H6("Chiffre d'affaires", style={
                                "fontWeight": "bold",
                                "color": "white",
                                "textAlign": "center"
                            }),
                            html.H1(id="carte_ca", style={
                                "color": "white",
                                "textAlign": "center",
                                "fontWeight": "bold"
                            }),
                            html.H5(id="var_ca", style={
                                "textAlign": "center",
                                "fontWeight": "bold"
                            })
                        ]),
                        style=style_carte_kpi
                    ),
                    md=6
                ),
                 # deuxième carte KPI pour le nombre de ventes
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("Décembre", style={
                                "color": "white",
                                "textAlign": "center",
                                "marginBottom": "5px"
                            }),
                            html.H6("Nombre de ventes", style={
                                "fontWeight": "bold",
                                "color": "white",
                                "textAlign": "center"
                            }),
                            html.H1(id="carte_nb", style={
                                "color": "white",
                                "textAlign": "center",
                                "fontWeight": "bold"
                            }),
                            html.H5(id="var_nb", style={
                                "textAlign": "center",
                                "fontWeight": "bold"
                            })
                        ]),
                        style=style_carte_kpi
                    ),
                    md=6
                )
            ], className="mb-4"),
             # carte pour le top 10 des ventes
            dbc.Card(
                dbc.CardBody([
                    html.Div("Fréquence des 10 meilleures ventes", style=style_titre_section),
                    dcc.Graph(id="graph_top10")
                ]),
                style={"borderRadius": "25px", "border": "none", "boxShadow": "0 4px 10px rgba(0,0,0,0.15)"}
            )
        ], md=5),

        #ici on a la partie droite pour le graphe d'évolution du CA et la table des ventes
        dbc.Col([

            dbc.Card(
                dbc.CardBody([
                    html.Div("Évolution du chiffre d'affaire par semaine", style=style_titre_section),
                    dcc.Graph(id="graph_ca")
                ]),
                style={"borderRadius": "25px", "border": "none", "boxShadow": "0 4px 10px rgba(0,0,0,0.15)"}
            ),
             # je mets un petit espace entre les deux cartes
            html.Br(),

            dbc.Card(
                dbc.CardBody([
                    html.Div("Table des 100 dernières ventes", style=style_titre_section),
                    dash_table.DataTable(
                        id="table_ventes",
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "center",
                            "padding": "10px"
                        },
                        style_header={
                            "fontWeight": "bold",
                            "backgroundColor": BLEU_NUIT,
                            "color": "white"
                        }
                    )
                ]),
                # je mets un style plus léger pour la carte de la table
                style={"borderRadius": "25px", "border": "none", "boxShadow": "0 4px 10px rgba(0,0,0,0.15)"}
            )
        ], md=7)

    ])
], fluid=True, style={"backgroundColor": "#0b1f3a", "minHeight": "100vh", "padding": "20px"})

# je définis les callback pour mettre à jour tous les éléments du dashboard en fonction de la zone sélectionnée
@app.callback(
    Output("carte_ca", "children"),
    Output("var_ca", "children"),
    Output("var_ca", "style"),
    Output("carte_nb", "children"),
    Output("var_nb", "children"),
    Output("var_nb", "style"),
    Output("graph_top10", "figure"),
    Output("graph_ca", "figure"),
    Output("table_ventes", "data"),
    Output("table_ventes", "columns"),
    Input("zone", "value")
)
def mettre_a_jour(zone):

    # filtre des données
    if zone == "All":
        dff = df.copy()
    else:
        dff = df[df["Location"] == zone].copy()

    # carte CA décembre
    ca_dec = ca_par_mois(dff, 12)
    ca_nov = ca_par_mois(dff, 11)
    diff_ca = ca_dec - ca_nov

    # carte nombre décembre
    nb_dec = len(dff[dff["Month"] == 12])
    nb_nov = len(dff[dff["Month"] == 11])
    diff_nb = nb_dec - nb_nov

    # texte variation CA
    if diff_ca < 0:
        texte_ca = "▼ " + str(round(diff_ca, 0))
        style_ca = {"color": "#ff6b6b", "textAlign": "center", "fontWeight": "bold"}
    else:
        texte_ca = "▲ " + str(round(diff_ca, 0))
        style_ca = {"color": "#7CFC98", "textAlign": "center", "fontWeight": "bold"}

    # texte variation nombre
    if diff_nb < 0:
        texte_nb = "▼ " + str(diff_nb)
        style_nb = {"color": "#ff6b6b", "textAlign": "center", "fontWeight": "bold"}
    else:
        texte_nb = "▲ " + str(diff_nb)
        style_nb = {"color": "#7CFC98", "textAlign": "center", "fontWeight": "bold"}

    # graphe top 10
    fig_top10 = barplot_top10_ventes(dff[dff["Month"] == 12])

    # graphe évolution CA
    fig_ca = plot_evolution_chiffre_affaire(dff)

    # table des ventes
    table = dff.sort_values("Transaction_Date", ascending=False).head(100).copy()

    colonnes_table = [
        "Transaction_Date", "Gender", "Location",
        "Product_Category", "Quantity", "Avg_Price", "Discount_pct"
    ]
    colonnes_table = [c for c in colonnes_table if c in table.columns]
    table = table[colonnes_table]

    data = table.to_dict("records")
    columns = [{"name": c, "id": c} for c in table.columns]

    return round(ca_dec, 0), texte_ca, style_ca, nb_dec, texte_nb, style_nb, fig_top10, fig_ca, data, columns


if __name__ == '__main__':
    app.run(debug=True)