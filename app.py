

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc


# data
df = pd.read_csv("data.csv")

# colonnes utiles
cols_utiles = [
    "CustomerID", "Gender", "Location", "Product_Category",
    "Quantity", "Avg_Price", "Transaction_Date", "Month", "Discount_pct"
]
cols_utiles = [c for c in cols_utiles if c in df.columns]
df = df[cols_utiles].copy()

# CustomerID
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


# fonctions
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

    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
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

    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
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
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
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
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return fig


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "ECAP Boutique"

app.layout = dbc.Container([

    # ligne titre + filtre
    dbc.Row([
        # colonne titre
        dbc.Col(
            html.H3("ECAP Store", style={"fontWeight": "bold", "marginTop": "10px"}),
            md=6
        ),

        # colonne filtre zone
        dbc.Col([
            html.Label("Choisissez une zone"),
            dcc.Dropdown(
                id="zone",
                options=[{"label": "All", "value": "All"}] + [{"label": x, "value": x} for x in locations],
                value="All",
                clearable=False
            )
        ], md=4)
    ], className="mb-3"),

    dbc.Row([

        # colonne gauche
        dbc.Col([

            # colonne cartes
            dbc.Row([
                # colonne carte CA
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("December"),
                            html.H1(id="carte_ca"),
                            html.H5(id="var_ca")
                        ])
                    ),
                    md=6
                ),

                # colonne carte ventes
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("December"),
                            html.H1(id="carte_nb"),
                            html.H5(id="var_nb")
                        ])
                    ),
                    md=6
                )
            ], className="mb-3"),

            # colonne top 10
            dbc.Card(
                dbc.CardBody([
                    html.H4("Fréquence des 10 meilleures ventes"),
                    dcc.Graph(id="graph_top10")
                ])
            )
        ], md=5),

        # colonne droite
        dbc.Col([

            # colonne courbe CA
            dbc.Card(
                dbc.CardBody([
                    html.H4("Évolution du chiffre d'affaire par semaine"),
                    dcc.Graph(id="graph_ca")
                ])
            ),

            html.Br(),

            # colonne table
            dbc.Card(
                dbc.CardBody([
                    html.H4("Table des 100 dernières ventes"),
                    dash_table.DataTable(
                        id="table_ventes",
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "center"},
                        style_header={"fontWeight": "bold"}
                    )
                ])
            )
        ], md=7)

    ])
], fluid=True)


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

    # colonne filtre des données
    if zone == "All":
        dff = df.copy()
    else:
        dff = df[df["Location"] == zone].copy()

    # colonne carte CA décembre
    ca_dec = ca_par_mois(dff, 12)
    ca_nov = ca_par_mois(dff, 11)
    diff_ca = ca_dec - ca_nov

    # colonne carte nombre décembre
    nb_dec = len(dff[dff["Month"] == 12])
    nb_nov = len(dff[dff["Month"] == 11])
    diff_nb = nb_dec - nb_nov

    # colonne texte variation CA
    if diff_ca < 0:
        texte_ca = "▼ " + str(round(diff_ca, 0))
        style_ca = {"color": "red"}
    else:
        texte_ca = "▲ " + str(round(diff_ca, 0))
        style_ca = {"color": "green"}

    # colonne texte variation nombre
    if diff_nb < 0:
        texte_nb = "▼ " + str(diff_nb)
        style_nb = {"color": "red"}
    else:
        texte_nb = "▲ " + str(diff_nb)
        style_nb = {"color": "green"}

    # colonne graphe top 10
    fig_top10 = barplot_top10_ventes(dff[dff["Month"] == 12])

    # colonne graphe évolution CA
    fig_ca = plot_evolution_chiffre_affaire(dff)

    # colonne table des ventes
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
    app.run_server(debug=True)