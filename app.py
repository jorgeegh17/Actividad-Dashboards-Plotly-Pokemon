"""
Pokemon Dashboard— Dash + Plotly
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ─── Carga de datos ───────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv('pokemon_complete.csv')
    df.columns = [c.strip() for c in df.columns]
    df['habitat'] = df['habitat'].fillna('Unknown')
    df['type_2']  = df['type_2'].fillna('—')
    return df

df = load_data()

gen_labels = {
    'gen-i': 'Gen I', 'gen-ii': 'Gen II', 'gen-iii': 'Gen III',
    'gen-iv': 'Gen IV', 'gen-v': 'Gen V', 'gen-vi': 'Gen VI',
    'gen-vii': 'Gen VII', 'gen-viii': 'Gen VIII', 'gen-ix': 'Gen IX',
}
df['gen_label'] = df['generation'].map(gen_labels)

# ─── Columnas derivadas (pokemon_jorge) ───────────────────────────────────────
df['poder_ofensivo']  = (df['attack'] + df['sp_attack']) / 2
df['poder_defensivo'] = (df['defense'] + df['sp_defense']) / 2

med_atk = df['poder_ofensivo'].median()
med_def = df['poder_defensivo'].median()

df['cuadrante'] = np.where(
    (df['poder_ofensivo'] >= med_atk) & (df['poder_defensivo'] >= med_def), 'Sweeper',
    np.where(
        (df['poder_ofensivo'] >= med_atk) & (df['poder_defensivo'] < med_def), 'Glass Cannon',
        np.where(
            (df['poder_ofensivo'] < med_atk) & (df['poder_defensivo'] >= med_def), 'Wall',
            'Pivot'
        )
    )
)

df['tier'] = np.where(df['base_stat_total'] < 400,  'Low Tier (<400)',
             np.where(df['base_stat_total'] <= 549, 'Mid Tier (400-549)', 'Top Tier (550+)'))

df['categoria'] = np.where(df['is_legendary'], 'Legendario',
                  np.where(df['is_mythical'],   'Mítico',
                  np.where(df['is_baby'],        'Baby', 'Normal')))

# ─── Paleta de tipos (adaptada a tema claro) ──────────────────────────────────
TYPE_COLORS = {
    'Normal': '#8a8868',   'Fire': '#d06828',    'Water': '#4870d0',
    'Electric': '#c8a820', 'Grass': '#588840',   'Ice': '#68b8b8',
    'Fighting': '#902020', 'Poison': '#802880',  'Ground': '#b09048',
    'Flying': '#7870c8',   'Psychic': '#d03868', 'Bug': '#787800',
    'Rock': '#888028',     'Ghost': '#503070',   'Dragon': '#5028c8',
    'Dark': '#503830',     'Steel': '#8888a8',   'Fairy': '#c07888',
}

# ─── Colores del tema claro ───────────────────────────────────────────────────
BG_COLOR   = '#FFFFFF'
CARD_COLOR = '#F8F8F8'
TEXT_COLOR = '#222222'
GRID_COLOR = '#E0E0E0'
ACCENT     = '#CC0000'
BORDER_COLOR = '#DDDDDD'

# ─── Paletas pokemon_jorge ────────────────────────────────────────────────────
paletas = {
    'Análogos':        ['#FF0000', '#930031', '#930000', '#933100', '#936200'],
    'Armónica':        ['#FF0000', '#930000', '#CC0000', '#FF4F30', '#FF845C'],
    'Base':            ['#FF0000', '#CC0000', '#3B4CCA', '#FFDE00', '#B3A125'],
    'Complementaria':  ['#FF0000', '#930031', '#009362', '#4FC490', '#7A9300'],
    'Triádica':        ['#FF0000', '#319300', '#003193', '#C9435A', '#5E000A'],
}

# ─── Helpers de layout para gráficas claras ───────────────────────────────────
def light_layout(**kwargs):
    base = dict(
        plot_bgcolor=CARD_COLOR,
        paper_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, family="'Segoe UI', sans-serif"),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_COLOR),
    )
    base.update(kwargs)
    return base

# ─── Gráfica 1: Scatter Attack vs Speed ──────────────────────────────────────
def make_scatter():
    fig = go.Figure()
    for t in sorted(df['type_1'].unique()):
        sub = df[df['type_1'] == t]
        color = TYPE_COLORS.get(t, '#888')
        fig.add_trace(go.Scatter(
            x=sub['speed'], y=sub['attack'],
            mode='markers', name=t,
            marker=dict(
                color=color,
                size=np.where(sub['is_legendary'] | sub['is_mythical'], 12, 7),
                symbol=np.where(sub['is_legendary'] | sub['is_mythical'], 'star', 'circle'),
                opacity=0.80,
                line=dict(width=0.5, color='rgba(0,0,0,0.2)'),
            ),
            customdata=np.stack([
                sub['name'], sub['type_1'], sub['type_2'],
                sub['hp'], sub['defense'], sub['sp_attack'],
                sub['sp_defense'], sub['base_stat_total'],
                np.where(sub['is_legendary'], '⭐ Legendary',
                         np.where(sub['is_mythical'], '✨ Mythical', '')),
            ], axis=-1),
            hovertemplate=(
                '<b>%{customdata[0]}</b> %{customdata[8]}<br>'
                'Tipo: %{customdata[1]} / %{customdata[2]}<br>'
                '─────────────────<br>'
                '⚔️ Ataque: <b>%{y}</b>  💨 Velocidad: <b>%{x}</b><br>'
                '❤️ HP: %{customdata[3]}  🛡️ Def: %{customdata[4]}<br>'
                '✨ SpAtk: %{customdata[5]}  🔮 SpDef: %{customdata[6]}<br>'
                'BST: <b>%{customdata[7]}</b><extra></extra>'
            ),
        ))
    fig.update_layout(
        **light_layout(
            legend=dict(bgcolor='rgba(255,255,255,0.8)', bordercolor=BORDER_COLOR, borderwidth=1),
            margin=dict(l=60, r=20, t=70, b=60),
            height=600,
        )
    )
    return fig


# ─── Gráfica 2: Heatmap stats por Tipo ───────────────────────────────────────
def make_heatmap():
    stats       = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
    stat_labels = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed']
    type_avg    = df.groupby('type_1')[stats].mean().round(1)
    type_avg    = type_avg.sort_values('speed', ascending=False)
    z           = type_avg.values
    types       = list(type_avg.index)
    z_norm      = (z - z.mean(axis=0)) / z.std(axis=0)
    hover = [[f'<b>{types[i]} — {stat_labels[j]}</b><br>Avg: {z[i][j]}'
              for j in range(len(stats))] for i in range(len(types))]
    fig = go.Figure(go.Heatmap(
        z=z_norm, x=stat_labels, y=types,
        text=[[f'{v:.0f}' for v in row] for row in z],
        texttemplate='%{text}',
        textfont=dict(size=11, color='#333333'),
        colorscale=[
            [0.0, '#f0f4ff'], [0.3, '#c8d8f8'], [0.5, '#90aee0'],
            [0.7, '#e87080'], [0.85, '#c83040'], [1.0, '#8b0000'],
        ],
        hovertext=hover,
        hovertemplate='%{hovertext}<extra></extra>',
        showscale=True,
        colorbar=dict(
            title=dict(text='Z-score', font=dict(color=TEXT_COLOR)),
            tickfont=dict(color=TEXT_COLOR),
        ),
    ))
    fig.update_layout(
        **light_layout(
            xaxis=dict(color=TEXT_COLOR, tickfont=dict(size=12), gridcolor=GRID_COLOR),
            yaxis=dict(color=TEXT_COLOR, tickfont=dict(size=11), gridcolor=GRID_COLOR),
            margin=dict(l=90, r=80, t=70, b=40),
            height=620,
        )
    )
    return fig


# ─── Gráfica 3: Violin BST por Generación ────────────────────────────────────
def make_violin():
    gen_order = ['gen-i','gen-ii','gen-iii','gen-iv','gen-v',
                 'gen-vi','gen-vii','gen-viii','gen-ix']
    colors = [
        '#d4a820','#58a840','#4870c8','#d06028',
        '#8870c0','#d83870','#68b8b8','#902020','#b09848',
    ]
    fig = go.Figure()
    for gen, color in zip(gen_order, colors):
        sub   = df[df['generation'] == gen]
        label = gen_labels.get(gen, gen)
        fig.add_trace(go.Violin(
            x=[label] * len(sub), y=sub['base_stat_total'],
            name=label,
            box_visible=True, meanline_visible=True,
            line_color=color, fillcolor=color,
            opacity=0.55,
            points='outliers',
            pointpos=0, jitter=0.3,
            marker=dict(color=color, size=4, opacity=0.6),
            hovertemplate=(
                f'<b>{label}</b><br>'
                'BST: <b>%{y}</b><extra></extra>'
            ),
        ))
    fig.update_layout(
        **light_layout(
            yaxis=dict(title='Base Stat Total', gridcolor=GRID_COLOR, color=TEXT_COLOR),
            xaxis=dict(color=TEXT_COLOR),
            showlegend=False, violinmode='overlay',
            margin=dict(l=60, r=20, t=70, b=40),
            height=550,
        )
    )
    return fig


# ─── Gráfica 4: Parallel Coordinates stats por Tipo ──────────────────────────
def make_parallel():
    stats       = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
    stat_labels = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed']
    N           = len(stats)
    xs          = list(range(N))
    type_avg    = df.groupby('type_1')[stats].mean().round(1).reset_index()
    mins        = type_avg[stats].min()
    maxs        = type_avg[stats].max()
    norm        = (type_avg[stats] - mins) / (maxs - mins)
    fig         = go.Figure()
    for i in range(N):
        fig.add_shape(type='line', x0=i, x1=i, y0=-0.05, y1=1.05,
                      line=dict(color=GRID_COLOR, width=1.5))
    for _, row in type_avg.iterrows():
        t     = row['type_1']
        color = TYPE_COLORS.get(t, '#888')
        ys    = norm.loc[row.name, stats].tolist()
        cd    = [[lbl, f'{row[s]:.0f}'] for lbl, s in zip(stat_labels, stats)]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode='lines+markers', name=t,
            line=dict(color=color, width=2.2),
            marker=dict(color=color, size=7,
                        line=dict(width=1, color='rgba(0,0,0,0.15)')),
            customdata=cd,
            hovertemplate=(
                f'<b style="color:{color}">{t}</b><br>'
                '%{customdata[0]}: <b>%{customdata[1]}</b>'
                '<extra></extra>'
            ),
            hoverlabel=dict(bgcolor='white', bordercolor=color,
                            font=dict(color=TEXT_COLOR, size=12)),
        ))
    annotations = []
    for i, (lbl, s) in enumerate(zip(stat_labels, stats)):
        annotations += [
            dict(x=i, y=1.13, xref='x', yref='paper', text=f'<b>{lbl}</b>',
                 showarrow=False, font=dict(size=13, color=ACCENT), xanchor='center'),
            dict(x=i, y=1.06, xref='x', yref='paper', text=f'{maxs[s]:.0f}',
                 showarrow=False, font=dict(size=9, color='rgba(0,0,0,0.4)'), xanchor='center'),
            dict(x=i, y=-0.06, xref='x', yref='paper', text=f'{mins[s]:.0f}',
                 showarrow=False, font=dict(size=9, color='rgba(0,0,0,0.4)'), xanchor='center'),
        ]
    fig.update_layout(
        **light_layout(
            xaxis=dict(tickvals=xs, showticklabels=False, range=[-0.3, N - 0.7],
                       showgrid=False, zeroline=False),
            yaxis=dict(range=[-0.12, 1.12], showgrid=False, zeroline=False, showticklabels=False),
            annotations=annotations,
            legend=dict(bgcolor='rgba(255,255,255,0.8)', bordercolor=BORDER_COLOR, borderwidth=1,
                        font=dict(size=10), x=1.01, y=0.5, xanchor='left', yanchor='middle'),
            hovermode='closest',
            margin=dict(l=40, r=130, t=110, b=40),
            height=580,
        )
    )
    return fig


# ─── Gráfica 5: Top 40 más rápidos (Bar) ─────────────────────────────────────
def make_speed_tier():
    top = df.nlargest(40, 'speed').copy().reset_index(drop=True)
    top['color'] = top['type_1'].map(TYPE_COLORS)
    top['label'] = top.apply(
        lambda r: '⭐' if r['is_legendary'] else ('✨' if r['is_mythical'] else ''), axis=1)
    fig = go.Figure()
    for spd in [100, 110, 120, 130]:
        fig.add_vline(x=spd, line_dash='dot', line_color='rgba(0,0,0,0.15)',
                      annotation_text=f'Base {spd}',
                      annotation_font_color='rgba(0,0,0,0.35)',
                      annotation_position='top right')
    fig.add_trace(go.Bar(
        x=top['speed'], y=top['name'], orientation='h',
        marker=dict(color=top['color'],
                    line=dict(width=0.5, color='rgba(0,0,0,0.1)'), opacity=0.85),
        customdata=np.stack([
            top['name'], top['type_1'], top['type_2'],
            top['attack'], top['sp_attack'], top['defense'],
            top['sp_defense'], top['hp'], top['base_stat_total'], top['label'],
        ], axis=-1),
        hovertemplate=(
            '<b>%{customdata[0]}</b> %{customdata[9]}<br>'
            'Tipo: %{customdata[1]} / %{customdata[2]}<br>'
            '─────────────────<br>'
            '💨 Speed: <b>%{x}</b><br>'
            '⚔️ Atk: %{customdata[3]}  ✨ SpAtk: %{customdata[4]}<br>'
            '🛡️ Def: %{customdata[5]}  🔮 SpDef: %{customdata[6]}<br>'
            '❤️ HP: %{customdata[7]}  BST: <b>%{customdata[8]}</b>'
            '<extra></extra>'
        ),
        text=top['speed'].astype(str), textposition='outside',
        textfont=dict(size=10, color=TEXT_COLOR),
    ))
    fig.update_layout(
        **light_layout(
            xaxis=dict(title='Velocidad base', gridcolor=GRID_COLOR, color=TEXT_COLOR, range=[0, 230]),
            yaxis=dict(autorange='reversed', tickfont=dict(size=11), color=TEXT_COLOR),
            showlegend=False,
            margin=dict(l=160, r=60, t=70, b=40),
            height=900,
        )
    )
    return fig


# ─── Gráfica 6: Scatter Ofensivo/Defensivo ───────────────────────────────────
def make_scatter_ofdef():
    color_map = {
        'Sweeper':      paletas['Análogos'][0],
        'Glass Cannon': paletas['Análogos'][1],
        'Wall':         paletas['Análogos'][2],
        'Pivot':        paletas['Análogos'][3],
    }
    fig = px.scatter(
        df,
        x='poder_ofensivo', y='poder_defensivo',
        color='cuadrante',
        color_discrete_map=color_map,
        hover_name='name',
        hover_data={'type_1': True, 'type_2': True,
                    'poder_ofensivo': ':.1f', 'poder_defensivo': ':.1f',
                    'base_stat_total': True, 'cuadrante': False},
        labels={'poder_ofensivo': 'Poder Ofensivo (ATK+SpATK)/2',
                'poder_defensivo': 'Poder Defensivo (DEF+SpDEF)/2',
                'cuadrante': 'Rol'},
        opacity=0.75,
    )
    fig.add_vline(x=med_atk, line_dash='dash', line_color='gray', opacity=0.4)
    fig.add_hline(y=med_def, line_dash='dash', line_color='gray', opacity=0.4)
    ann = dict(showarrow=False, font=dict(size=12, color='black'),
               bgcolor='rgba(0,0,0,0.07)', borderpad=4)
    fig.add_annotation(x=df['poder_ofensivo'].max()*0.93,
                       y=df['poder_defensivo'].max()*0.95, text='Sweeper', **ann)
    fig.add_annotation(x=df['poder_ofensivo'].max()*0.93,
                       y=df['poder_defensivo'].min()+5,    text='Glass Cannon', **ann)
    fig.add_annotation(x=df['poder_ofensivo'].min()+2,
                       y=df['poder_defensivo'].max()*0.95, text='Wall', **ann)
    fig.add_annotation(x=df['poder_ofensivo'].min()+2,
                       y=df['poder_defensivo'].min()+5,    text='Pivot', **ann)
    fig.update_traces(marker=dict(size=6))
    fig.update_layout(
        **light_layout(
            legend_title_text='Rol Estratégico',
            height=550,
        )
    )
    return fig


# ─── Gráfica 7: Violin capture_rate por Tier ─────────────────────────────────
def make_violin_capture():
    color_map = {
        'Low Tier (<400)':    paletas['Armónica'][4],
        'Mid Tier (400-549)': paletas['Armónica'][2],
        'Top Tier (550+)':    paletas['Armónica'][1],
    }
    fig = px.violin(
        df,
        x='tier', y='capture_rate',
        color='tier',
        color_discrete_map=color_map,
        box=True, points='all',
        hover_name='name',
        hover_data={'capture_rate': True, 'base_stat_total': True,
                    'type_1': True, 'tier': False},
        labels={'capture_rate': 'Tasa de Captura', 'tier': 'Tier de Poder'},
        category_orders={'tier': ['Low Tier (<400)', 'Mid Tier (400-549)', 'Top Tier (550+)']},
    )
    for tier_name, color in color_map.items():
        median_val = df[df['tier'] == tier_name]['capture_rate'].median()
        fig.add_annotation(
            x=tier_name, y=median_val + 8,
            text=f'Md: {median_val:.0f}',
            showarrow=False,
            font=dict(size=11, color=color),
            borderpad=3,
        )
    fig.update_traces(meanline_visible=True, jitter=0.3, marker_size=3, opacity=0.8)
    fig.update_layout(
        **light_layout(
            showlegend=False,
            height=550,
        )
    )
    return fig


# ─── Gráfica 8: Proporción por Generación (Donut) ────────────────────────────
def make_pie_gen():
    gen_counts = df['generation'].value_counts().reset_index()
    gen_counts.columns = ['generation', 'count']
    gen_labels_full = {
        'gen-i': 'Gen I (Kanto)',     'gen-ii':   'Gen II (Johto)',
        'gen-iii': 'Gen III (Hoenn)', 'gen-iv':   'Gen IV (Sinnoh)',
        'gen-v':  'Gen V (Unova)',    'gen-vi':   'Gen VI (Kalos)',
        'gen-vii': 'Gen VII (Alola)', 'gen-viii': 'Gen VIII (Galar)',
        'gen-ix': 'Gen IX (Paldea)',
    }
    gen_counts['label'] = gen_counts['generation'].map(gen_labels_full)
    gen_colors_list = (paletas['Base'] * 2)[:len(gen_counts)]
    fig = go.Figure(go.Pie(
        labels=gen_counts['label'],
        values=gen_counts['count'],
        hole=0.45,
        marker=dict(colors=gen_colors_list, line=dict(color='white', width=2)),
        hovertemplate='<b>%{label}</b><br>Pokémon: %{value}<br>%{percent}<extra></extra>',
        textinfo='label+percent',
        textfont_size=11,
    ))
    fig.update_layout(
        **light_layout(
            legend=dict(orientation='v', x=1.02, y=0.5),
            annotations=[dict(text='1,350<br>Pokémon', x=0.5, y=0.5,
                              font=dict(size=16), showarrow=False)],
            height=550,
        )
    )
    return fig


# ─── Gráfica 9: Legendarios/Míticos por Generación ───────────────────────────
def make_bar_legendarios():
    cat_gen = df.groupby(['generation', 'categoria']).size().reset_index(name='count')
    gen_labels_short = {
        'gen-i': 'Gen I', 'gen-ii': 'Gen II', 'gen-iii': 'Gen III',
        'gen-iv': 'Gen IV', 'gen-v': 'Gen V', 'gen-vi': 'Gen VI',
        'gen-vii': 'Gen VII', 'gen-viii': 'Gen VIII', 'gen-ix': 'Gen IX',
    }
    cat_gen['gen_label'] = cat_gen['generation'].map(gen_labels_short)
    gen_order = ['Gen I','Gen II','Gen III','Gen IV','Gen V',
                 'Gen VI','Gen VII','Gen VIII','Gen IX']
    cat_order = ['Normal', 'Legendario', 'Mítico', 'Baby']
    color_map = {
        'Normal':     paletas['Complementaria'][0],
        'Legendario': paletas['Complementaria'][1],
        'Mítico':     paletas['Complementaria'][2],
        'Baby':       paletas['Complementaria'][3],
    }
    fig = px.bar(
        cat_gen,
        x='gen_label', y='count',
        color='categoria',
        color_discrete_map=color_map,
        category_orders={'gen_label': gen_order, 'categoria': cat_order},
        labels={'count': 'Número de Pokémon', 'gen_label': 'Generación',
                'categoria': 'Categoría'},
        text_auto=True,
        barmode='stack',
    )
    fig.update_traces(
        textfont_size=10,
        hovertemplate='<b>%{x}</b><br>Categoría: %{fullData.name}<br>Cantidad: %{y}<extra></extra>',
    )
    fig.update_layout(
        **light_layout(
            legend_title_text='Categoría',
            xaxis_title='Generación',
            yaxis_title='Número de Pokémon',
            height=550,
        )
    )
    return fig


# ─── Gráfica 10: Pokémon por Habitat ─────────────────────────────────────────
def make_bar_habitat():
    hab_type = df[df['habitat'] != 'Unknown'].groupby(
        ['habitat', 'type_1']).size().reset_index(name='count')
    top_types = df['type_1'].value_counts().head(10).index.tolist()
    hab_type_filt = hab_type[hab_type['type_1'].isin(top_types)].copy()
    hab_labels = {
        'grassland': 'Pradera',    'mountain':      'Montaña',
        'waters-edge': 'Orilla',   'forest':        'Bosque',
        'rough-terrain': 'T. Rugoso', 'cave':       'Cueva',
        'urban': 'Urbano',         'sea':           'Mar',
        'rare': 'Raro',
    }
    hab_type_filt['habitat_label'] = hab_type_filt['habitat'].map(
        lambda x: hab_labels.get(x, x))
    type_list = hab_type_filt['type_1'].unique().tolist()
    color_map = {t: paletas['Triádica'][i % len(paletas['Triádica'])]
                 for i, t in enumerate(type_list)}
    fig = px.bar(
        hab_type_filt,
        x='habitat_label', y='count',
        color='type_1',
        color_discrete_map=color_map,
        barmode='group',
        labels={'count': 'Número de Pokémon', 'habitat_label': 'Habitat',
                'type_1': 'Tipo Primario'},
        hover_data={'count': True, 'type_1': True},
    )
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Tipo: %{fullData.name}<br>Pokémon: %{y}<extra></extra>',
    )
    fig.update_layout(
        **light_layout(
            legend_title_text='Tipo Primario',
            xaxis=dict(title='Habitat', tickangle=-25, gridcolor=GRID_COLOR, color=TEXT_COLOR),
            yaxis_title='Número de Pokémon',
            bargap=0.15, bargroupgap=0.05,
            height=550,
        )
    )
    return fig


# ─── Catálogo de gráficas ─────────────────────────────────────────────────────
CHARTS = [
    {'label': '1.  Attack vs Speed (Scatter)',            'value': 'scatter'},
    {'label': '2.  Stats por Tipo (Heatmap)',              'value': 'heatmap'},
    {'label': '3.  BST por Generación (Violin)',            'value': 'violin'},
    {'label': '4.  Stats promedio por Tipo (Parallel)',     'value': 'parallel'},
    {'label': '5.  Top 40 más rápidos (Bar)',               'value': 'speed'},
    {'label': '6.  Ofensivo vs Defensivo (Scatter)',        'value': 'scatter_ofdef'},
    {'label': '7.  Capture Rate por Tier (Violin)',         'value': 'violin_capture'},
    {'label': '8.  Proporción por Generación (Donut)',      'value': 'pie_gen'},
    {'label': '9.  Legendarios por Generación (Stacked)',   'value': 'bar_legendarios'},
    {'label': '10. Pokémon por Habitat (Bar)',              'value': 'bar_habitat'},
]

TITLES = {
    'scatter':          'Attack vs Speed — por Tipo primario',
    'heatmap':          'Promedio de stats por Tipo principal',
    'violin':           'Distribución de stats base por Generación',
    'parallel':         'Stats promedio por Tipo',
    'speed':            'Top 40 Pokémon más rápidos',
    'scatter_ofdef':    'Poder Ofensivo vs Defensivo — Roles estratégicos',
    'violin_capture':   'Tasa de Captura por Tier de Poder',
    'pie_gen':          'Proporción de Pokémon por Generación',
    'bar_legendarios':  'Legendarios, Míticos y Normales por Generación',
    'bar_habitat':      'Distribución de Tipos por Habitat',
}

BUILDERS = {
    'scatter':         make_scatter,
    'heatmap':         make_heatmap,
    'violin':          make_violin,
    'parallel':        make_parallel,
    'speed':           make_speed_tier,
    'scatter_ofdef':   make_scatter_ofdef,
    'violin_capture':  make_violin_capture,
    'pie_gen':         make_pie_gen,
    'bar_legendarios': make_bar_legendarios,
    'bar_habitat':     make_bar_habitat,
}

DESCRIPTIONS = {

    'scatter': """
## 1. Attack vs Speed — Scatter Plot

### ¿Qué muestra?
Esta gráfica compara la relación entre la velocidad (`Speed`)
y el ataque físico (`Attack`) de los Pokémon.

Cada punto representa un Pokémon y está coloreado según su tipo primario.

Los Pokémon legendarios y míticos se distinguen mediante símbolos especiales.

---

###  Paleta utilizada
Se utiliza una paleta categórica basada en los colores clásicos
de cada tipo Pokémon (`TYPE_COLORS`).

Ejemplos:
- Fire → rojo/naranja
- Water → azul
- Grass → verde
- Electric → amarillo

---

### Interpretación
La gráfica permite identificar Pokémon rápidos y ofensivos,
así como observar tendencias entre tipos.

Tipos como:
- **Electric** y **Flying** tienden a velocidades altas.
- **Rock** y **Steel** suelen tener baja velocidad.

Los outliers representan Pokémon excepcionalmente fuertes,
generalmente legendarios.
""",

    'heatmap': """
## 2. Stats por Tipo — Heatmap

### ¿Qué muestra?
La gráfica representa el promedio de estadísticas base
para cada tipo Pokémon.

Cada fila corresponde a un tipo y cada columna a una estadística:
HP, Attack, Defense, Sp. Atk, Sp. Def y Speed.

---

###  Paleta utilizada
Se utiliza una escala secuencial divergente:
- tonos claros → valores bajos,
- tonos intensos → valores altos.

La escala está normalizada mediante **Z-score**,
permitiendo comparar estadísticas relativas entre tipos.

---

### Interpretación
Tipos como:
- **Dragon**
- **Steel**
- **Psychic**

presentan estadísticas consistentemente altas.

En cambio:
- **Bug**
- **Normal**

muestran valores más equilibrados o moderados.

El heatmap facilita detectar fortalezas y debilidades
de cada tipo rápidamente.
""",

    'violin': """
## 3. BST por Generación — Violin Plot

### ¿Qué muestra?
La gráfica muestra la distribución del poder total (`Base Stat Total`)
para cada generación Pokémon.

Cada violín representa la densidad y dispersión
de estadísticas dentro de una generación.

---

###  Paleta utilizada
Se emplea una paleta categórica multicolor,
asignando un color distinto a cada generación.

La transparencia ayuda a visualizar concentración y outliers.

---

### Interpretación
Las generaciones recientes presentan mayor variabilidad,
indicando diseños más diversos.

Los puntos extremos suelen corresponder a:
- legendarios,
- mega evoluciones,
- formas especiales.

La anchura del violín indica dónde se concentra
la mayor cantidad de Pokémon.
""",

    'parallel': """
## 4. Stats promedio por Tipo — Parallel Coordinates

### ¿Qué muestra?
La gráfica compara simultáneamente múltiples estadísticas promedio
entre tipos Pokémon.

Cada línea representa un tipo diferente.

---

###  Paleta utilizada
Se utiliza la paleta `TYPE_COLORS`,
manteniendo coherencia visual con los tipos Pokémon oficiales.

Cada línea conserva el color asociado a su tipo.

---

### Interpretación
Permite identificar perfiles estratégicos:

- **Steel** domina defensa.
- **Electric** sobresale en velocidad.
- **Dragon** mantiene estadísticas balanceadas.

Es útil para comparar fortalezas relativas
entre múltiples atributos al mismo tiempo.
""",

    'speed': """
## 5. Top 40 Pokémon más rápidos

### ¿Qué muestra?
La gráfica ordena los 40 Pokémon con mayor velocidad base.

Cada barra representa un Pokémon individual.

---

###  Paleta utilizada
Los colores corresponden al tipo primario de cada Pokémon,
utilizando `TYPE_COLORS`.

Las líneas verticales marcan referencias competitivas importantes:
100, 110, 120 y 130 de velocidad base.

---

### Interpretación
La velocidad determina qué Pokémon ataca primero en combate.

Se observa predominancia de:
- Electric,
- Flying,
- Dragon.

Muchos Pokémon legendarios aparecen en los valores superiores,
confirmando su ventaja competitiva.
""",

    'scatter_ofdef': """
## 6. Poder Ofensivo vs Defensivo

### ¿Qué muestra?
La gráfica compara el poder ofensivo promedio
contra el poder defensivo promedio de cada Pokémon.

Los cuadrantes representan distintos roles estratégicos.

---

###  Paleta utilizada
Se utiliza una paleta análoga derivada de tonos rojos
para diferenciar:
- Sweeper,
- Glass Cannon,
- Wall,
- Pivot.

---

### Interpretación
La mayoría de Pokémon pertenecen al cuadrante **Pivot**,
indicando estadísticas moderadas.

Los **Glass Cannon** poseen alto daño pero poca resistencia.

Los **Sweepers** son raros,
ya que combinar ataque y defensa elevados
es característico de Pokémon legendarios.
""",

    'violin_capture': """
## 7. Capture Rate por Tier

### ¿Qué muestra?
La gráfica analiza la distribución de tasas de captura
según el tier de poder del Pokémon.

---

###  Paleta utilizada
Se utiliza una paleta armónica en tonos rojos,
donde cada tier tiene una intensidad distinta.

---

### Interpretación
Existe una relación inversa clara:
a mayor poder, menor tasa de captura.

Los Pokémon Top Tier presentan valores muy bajos,
reflejando una mecánica deliberada de rareza y dificultad.
""",

    'pie_gen': """
## 8. Proporción por Generación

### ¿Qué muestra?
La gráfica donut representa la proporción de Pokémon
introducidos en cada generación.

---

###  Paleta utilizada
Se utiliza la paleta `Base`,
combinando colores inspirados en Pokémon:
rojo, azul y amarillo.

---

### Interpretación
La Generación V contiene la mayor cantidad de Pokémon,
mientras que Kalos tiene la menor.

Esto refleja cambios en la estrategia de diseño
de Game Freak a lo largo del tiempo.
""",

    'bar_legendarios': """
## 9. Categorías por Generación

### ¿Qué muestra?
La gráfica muestra la cantidad de Pokémon:
- normales,
- legendarios,
- míticos,
- baby

por generación.

---

###  Paleta utilizada
Se utiliza una paleta complementaria
para diferenciar claramente cada categoría.

---

### Interpretación
Los Pokémon normales dominan todas las generaciones.

Las generaciones recientes introducen más legendarios,
mientras que los Pokémon Baby se concentran
en generaciones antiguas.
""",

    'bar_habitat': """
## 10. Pokémon por Habitat

### ¿Qué muestra?
La gráfica analiza la distribución de tipos Pokémon
según su habitat natural.

---

###  Paleta utilizada
Se utiliza una paleta triádica
para maximizar contraste entre tipos.

---

### Interpretación
Los habitats:
- waters-edge,
- grassland

presentan la mayor diversidad de especies.

Los habitats extremos como cuevas
muestran predominancia de tipos específicos
como Rock y Ground.
""",
}

# ─── Layout ───────────────────────────────────────────────────────────────────
app = Dash(__name__)

app.layout = html.Div(
    style={
        'backgroundColor': BG_COLOR,
        'minHeight': '100vh',
        'fontFamily': "'Segoe UI', sans-serif",
        'padding': '24px',
        'color': TEXT_COLOR,
    },
    children=[
        # Header
        html.Div(
            style={
                'display': 'flex', 'alignItems': 'center',
                'marginBottom': '24px',
                'borderBottom': f'2px solid {BORDER_COLOR}',
                'paddingBottom': '16px',
            },
            children=[
                html.Span('', style={'fontSize': '36px', 'marginRight': '12px'}),
                html.Div([
                    html.H1('Pokémon Complete Pokédex — Dashboard',
                            style={'color': ACCENT, 'margin': 0,
                                   'fontSize': '26px', 'fontWeight': '700'}),
                    html.P('Análisis de stats, tipos y generaciones  •  '
                           'Integrantes: Jorge Emiliano Gómez Hernández · Jaime Trujillo Ruiz',
                           style={'color': '#888', 'margin': 0, 'fontSize': '13px'}),
                ]),
            ],
        ),

        # Selector
        html.Div(
            style={'display': 'flex', 'alignItems': 'center',
                   'gap': '16px', 'marginBottom': '16px'},
            children=[
                html.Label('Selecciona un gráfico:',
                           style={'color': TEXT_COLOR, 'fontWeight': '600',
                                  'fontSize': '14px', 'whiteSpace': 'nowrap'}),
                dcc.Dropdown(
                    id='chart-selector',
                    options=CHARTS,
                    value='scatter',
                    clearable=False,
                    style={
                        'width': '400px',
                        'borderRadius': '8px',
                    },
                ),
            ],
        ),

        # Título dinámico
        html.H2(
            id='chart-title',
            style={'color': ACCENT, 'fontSize': '20px', 'fontWeight': '600',
                   'margin': '0 0 12px 4px'},
        ),

        # Contenedor del gráfico
        html.Div(
            style={
                'backgroundColor': CARD_COLOR,
                'borderRadius': '12px',
                'padding': '12px',
                'border': f'1px solid {BORDER_COLOR}',
                'boxShadow': '0 1px 6px rgba(0,0,0,0.06)',
            },
            children=[dcc.Graph(id='main-chart', config={'displayModeBar': True})],
        ),

        # Descripción dinámica (solo se muestra si hay texto)
        dcc.Markdown(
            id='chart-description',
            style={
                'maxWidth': '800px',
                'margin': '20px auto',
                'padding': '15px',
                'backgroundColor': '#fff5f5',
                'borderRadius': '8px',
                'borderLeft': '4px solid #CC0000',
                'display': 'none',
            },
        ),

        # Footer
        html.P(
            f"Dataset: {len(df)} Pokémon  •  {df['generation'].nunique()} generaciones  •  "
            f"{df['type_1'].nunique()} tipos",
            style={'color': '#aaa', 'fontSize': '12px',
                   'textAlign': 'center', 'marginTop': '16px'},
        ),
    ],
)

# ─── Callbacks ────────────────────────────────────────────────────────────────
@app.callback(
    Output('main-chart',       'figure'),
    Output('chart-title',      'children'),
    Output('chart-description', 'children'),
    Output('chart-description', 'style'),
    Input('chart-selector',    'value'),
)
def update_chart(chart_id):
    fig   = BUILDERS[chart_id]()
    title = TITLES[chart_id]
    desc  = DESCRIPTIONS.get(chart_id)

    base_style = {
        'maxWidth': '800px', 'margin': '20px auto',
        'padding': '15px', 'backgroundColor': '#fff5f5',
        'borderRadius': '8px', 'borderLeft': '4px solid #CC0000',
    }
    if desc:
        style = {**base_style, 'display': 'block'}
    else:
        style = {**base_style, 'display': 'none'}

    return fig, title, desc or '', style


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
