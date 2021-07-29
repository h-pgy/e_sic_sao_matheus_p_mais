import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

def calc_valores_acumulados_por_proposta(df):
    '''Calcula os valores acumulados por proposta. A coluna 
    count deve conter o resultado da contagem de algum agrupamento'''
    
    df = df.copy()
    
    df['acumulado'] = 0
    titulo = df.iloc[0]['Proposta']
    acumulado = df.iloc[0]['count']

    for i, row in df.iterrows():
        novo_titulo = row['Proposta']
        if titulo == novo_titulo:
            acumulado+=row['count']
            df.loc[i, 'acumulado'] = acumulado
        else:
            acumulado=row['count']
            df.loc[i, 'acumulado'] = acumulado
            titulo = novo_titulo
            
            
    return df

def preencher_vazios_acumulado(df):
    
    df = df.copy()
    dias = df.index
    df.reset_index(drop=True, inplace=True)

    for i, row in df.iterrows():
        for col in df.columns:
            if pd.isnull(row[col]):
                if i==0:
                    df.loc[i, col] = 0
                else:
                    df.loc[i, col] = df.loc[i-1, col]
    
    df.set_index(dias, inplace=True)
    
    return df

df = pd.read_csv('dados_abertos_votacao_sao_mateus.csv', sep=';')
df['count'] = 1
resultado_eleicao = df.groupby('Título').count()[['count']].sort_values(by='count', ascending = False)
posicoes = list(range(1, len(resultado_eleicao)+1))
resultado_eleicao['posicao'] = posicoes
df['Data do voto'] = df['Data do voto'] + '-' + df['Horário']
df['Data do voto'] = pd.to_datetime(df['Data do voto'], dayfirst=True)
votos_por_dia = df.groupby(['Título', 'Data do voto']).count()[['count']].reset_index()
votos_por_dia.rename({'Título' : 'Proposta'}, axis = 1, inplace=True)
votos_por_dia = calc_valores_acumulados_por_proposta(votos_por_dia)
votos_por_dia = votos_por_dia.pivot(index='Data do voto', columns='Proposta', values='acumulado')
votos_por_dia = preencher_vazios_acumulado(votos_por_dia)


app = dash.Dash(__name__)
server = app.server
app.title='Evolução da votação - São Mateus'

app.layout = html.Div([
    html.H1('Evolução da votação - São Mateus'),
    dcc.Graph(id="line-chart"),
    dcc.Slider(
        id="checklist",
        min = resultado_eleicao['posicao'].min(),
        max = resultado_eleicao['posicao'].max(),
        marks={i: '{}º lugar'.format(i) for i in resultado_eleicao['posicao']},
        value=3,
    )
])

@app.callback(
    Output("line-chart", "figure"), 
    [Input("checklist", "value")])
def update_line_chart(value):
    mask = resultado_eleicao['posicao']<=value
    propostas = resultado_eleicao[mask].index
    data = votos_por_dia[propostas]
    fig = px.line(data)
    return fig

if __name__ == "__main__":

    app.run_server(port=8052, debug=True)