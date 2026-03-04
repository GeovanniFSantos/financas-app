import streamlit as st
import plotly.express as px

def exibir_grafico_gastos(df_pizza):
    if df_pizza.empty:
        st.info("Sem despesas registradas para gerar o gráfico.")
        return

    # Criando o gráfico de pizza (Donut chart para ficar moderno)
    fig = px.pie(
        df_pizza, 
        values='total', 
        names='categoria', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Ajustes de layout
    fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
    fig.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)