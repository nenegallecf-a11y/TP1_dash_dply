import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc

df = pd.read_csv("data.csv")

df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")
df = df.dropna(subset=["Transaction_Date"]).copy()

if "Month" not in df.columns:
    df["Month"] = df["Transaction_Date"].dt.month
df["Month"] = df["Month"].astype(int)

df["Chiffre_affaire"] = df["Quantity"] * df["Avg_Price"] * (1 - df["Discount_pct"] / 100)
df["Week"] = df["Transaction_Date"].dt.to_period("W").dt.start_time

locations = sorted(df["Location"].dropna().unique().tolist())

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "ECAP Store"

BG = "#EAF3FB"
CARD_BG = "white"
TEXT_MUTED = "#6b7280"


def format_k(x):
    return f"{x/1000:.0f}k" if abs(x) >= 1000 else f"{x:.0f}"


def make_card(title, value, delta, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, style={"fontSize": "13px", "color": TEXT_MUTED}),
            html.Div(value, style={"fontSize": "42px", "fontWeight": "800", "lineHeight": "1.0"}),
            html.Div(delta, style={"fontSize": "13px", "fontWeight": "700", "color": color}),
        ]),
        style={
            "backgroundColor": CARD_BG,
            "border": "0",
            "borderRadius": "14px",
            "boxShadow": "0 10px 24px rgba(0,0,0,0.08)",
        }
    )


def make_panel(title, content, extra_style=None):
    style = {
        "backgroundColor": CARD_BG,
        "border": "0",
        "borderRadius": "14px",
        "boxShadow": "0 10px 24px rgba(0,0,0,0.08)",
    }
    if extra_style:
        style.update(extra_style)

    return dbc.Card(
        dbc.CardBody([
            html.Div(title, style={"fontWeight": "800", "marginBottom": "6px"}),
            content
        ]),
        style=style
    )


app.layout = dbc.Container(
    style={"backgroundColor": BG, "minHeight": "100vh", "padding": "18px"},
    children=[
        dbc.Row([
            dbc.Col(
                html.Div("ECAP Store", style={"fontSize": "18px", "fontWeight": "900"}),
                width=6
            ),
            dbc.Col(
                html.Div([
                    html.Div(
                        "Choisissez une zone",
                        style={"fontSize": "12px", "color": TEXT_MUTED, "marginBottom": "4px"}
                    ),
                    dcc.Dropdown(
                        id="loc-dd",
                        options=[{"label": "All", "value": "All"}] + [{"label": x, "value": x} for x in locations],
                        value="All",
                        clearable=False
                    ),
                ], style={"maxWidth": "320px", "marginLeft": "auto"}),
                width=6
            )
        ], align="center", className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(html.Div(id="kpi1"), md=6),
                    dbc.Col(html.Div(id="kpi2"), md=6),
                ], className="g-3 mb-3"),

                make_panel(
                    "Fréquence des 10 meilleures ventes",
                    dcc.Graph(
                        id="bar-top10",
                        config={"displayModeBar": False},
                        style={"height": "310px"}
                    ),
                    extra_style={"marginTop": "26px"}
                )
            ], md=5),

            dbc.Col([
                make_panel(
                    "Évolution du chiffre d’affaire par semaine",
                    dcc.Graph(
                        id="line-week",
                        config={"displayModeBar": False},
                        style={"height": "320px"}
                    )
                ),
                html.Div(style={"height": "12px"}),
                make_panel(
                    "Table des 100 dernières ventes",
                    html.Div([
                        dcc.Input(
                            id="table-filter",
                            placeholder="filtrer...",
                            type="text",
                            style={
                                "width": "220px",
                                "padding": "6px 10px",
                                "borderRadius": "10px",
                                "border": "1px solid #d1d5db",
                                "marginBottom": "10px"
                            }
                        ),
                        dash_table.DataTable(
                            id="sales-table",
                            page_size=10,
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            style_header={"backgroundColor": "#f3f4f6", "fontWeight": "800"},
                            style_cell={"fontFamily": "Arial", "fontSize": "12px", "padding": "8px"},
                        )
                    ])
                )
            ], md=7)
        ], className="g-3")
    ]
)


@app.callback(
    Output("kpi1", "children"),
    Output("kpi2", "children"),
    Output("bar-top10", "figure"),
    Output("line-week", "figure"),
    Output("sales-table", "data"),
    Output("sales-table", "columns"),
    Input("loc-dd", "value"),
    Input("table-filter", "value")
)
def update_dashboard(loc, q):
    if loc != "All":
        dloc = df[df["Location"] == loc].copy()
    else:
        dloc = df.copy()

    dec = dloc[dloc["Month"] == 12].copy()
    nov = dloc[dloc["Month"] == 11].copy()

    ca_dec = dec["Chiffre_affaire"].sum()
    ca_nov = nov["Chiffre_affaire"].sum()
    delta_ca = ca_dec - ca_nov

    if "Transaction_ID" in dec.columns:
        n_dec = dec["Transaction_ID"].nunique()
        n_nov = nov["Transaction_ID"].nunique()
    else:
        n_dec = len(dec)
        n_nov = len(nov)

    delta_n = n_dec - n_nov

    txt_ca = f"▲ {format_k(delta_ca)}" if delta_ca >= 0 else f"▼ {format_k(delta_ca)}"
    txt_n = f"▲ {delta_n}" if delta_n >= 0 else f"▼ {delta_n}"

    kpi1 = make_card("December", format_k(ca_dec), txt_ca, "green" if delta_ca >= 0 else "red")
    kpi2 = make_card("December", f"{n_dec}", txt_n, "green" if delta_n >= 0 else "red")

    d = dec
    prod_col = "Product_Description" if "Product_Description" in d.columns else "Product_Category"

    totals = d.groupby(prod_col)["Quantity"].sum().sort_values(ascending=False)
    top10 = totals.head(10).index.tolist()

    top = (
        d[d[prod_col].isin(top10)]
        .groupby([prod_col, "Gender"])["Quantity"]
        .sum()
        .reset_index()
    )

    order_asc = totals.loc[top10].sort_values(ascending=True).index.tolist()

    fig_bar = px.bar(
        top,
        x="Quantity",
        y=prod_col,
        color="Gender",
        orientation="h",
        barmode="group",
        category_orders={prod_col: order_asc}
    )
    fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10))

    weekly = (
        dloc.groupby("Week")["Chiffre_affaire"]
        .sum()
        .reset_index()
        .sort_values("Week")
    )

    fig_line = px.line(weekly, x="Week", y="Chiffre_affaire")
    fig_line.update_layout(margin=dict(l=10, r=10, t=10, b=10))

    cols = [
        "Transaction_Date",
        "Gender",
        "Location",
        "Product_Category",
        "Quantity",
        "Avg_Price",
        "Discount_pct"
    ]

    t = d.sort_values("Transaction_Date", ascending=False).head(100).copy()

    if q and str(q).strip():
        qq = str(q).strip().lower()
        mask = t[cols].astype(str).apply(lambda row: qq in " ".join(row.values).lower(), axis=1)
        t = t[mask]

    t["Transaction_Date"] = t["Transaction_Date"].dt.strftime("%Y-%m-%d")

    t = t[cols].rename(columns={
        "Transaction_Date": "Date",
        "Product_Category": "Product Category",
        "Avg_Price": "Avg Price",
        "Discount_pct": "Discount Pct"
    })

    data = t.to_dict("records")
    columns = [{"name": c, "id": c} for c in t.columns]

    return kpi1, kpi2, fig_bar, fig_line, data, columns




# execution de l'app
if __name__ == "__main__":
    app.run(debug=True, port=8051, jupyter_mode="external")