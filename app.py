import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Arquivos CSV
ENTRADA_CSV = 'entrada_vasilhames.csv'
SAIDA_CSV = 'saida_vasilhames.csv'

# Inicializar arquivos


def inicializar_arquivos():
    if not os.path.exists(ENTRADA_CSV):
        pd.DataFrame(columns=['Data', 'Turno', 'Operador', 'Máquina', 'Código',
                     'ML', 'Cor', 'Gr', 'Quantidade', 'Tipo']).to_csv(ENTRADA_CSV, index=False)
    if not os.path.exists(SAIDA_CSV):
        pd.DataFrame(columns=['Data', 'Operador', 'Código', 'ML', 'Produção',
                     'Perdas', 'Quarentena']).to_csv(SAIDA_CSV, index=False)


inicializar_arquivos()

# MENU lateral
st.sidebar.title("📦 Controle de Vasilhames - Sopro")
opcao = st.sidebar.radio("Escolha uma opção:", [
    "Registrar Entrada", "Registrar Saída", "Consultar Saldo", "Enviar por E-mail"
])

# REGISTRAR ENTRADA
if opcao == "Registrar Entrada":
    st.header("🔵 Registro de Entrada")
    with st.form("form_entrada"):
        data = st.date_input("Data", value=datetime.today())
        turno = st.selectbox("Turno", ["1", "2", "3"])
        operador = st.text_input("Operador")
        maquina = st.text_input("Máquina")
        codigo = st.text_input("Código")
        ml = st.text_input("ML")
        cor = st.text_input("Cor")
        gr = st.text_input("Gramatura")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        tipo = "Entrada"
        submit = st.form_submit_button("Registrar")

        if submit:
            novo = pd.DataFrame([[data.strftime("%d/%m/%Y"), turno, operador, maquina, codigo, ml, cor, gr, quantidade, tipo]],
                                columns=['Data', 'Turno', 'Operador', 'Máquina', 'Código', 'ML', 'Cor', 'Gr', 'Quantidade', 'Tipo'])
            novo.to_csv(ENTRADA_CSV, mode='a', header=False, index=False)
            st.success("✅ Entrada registrada com sucesso!")

# REGISTRAR SAÍDA
elif opcao == "Registrar Saída":
    st.header("🔴 Registro de Saída")
    with st.form("form_saida"):
        data = st.date_input("Data", value=datetime.today())
        operador = st.text_input("Operador")
        codigo = st.text_input("Código")
        ml = st.text_input("ML")
        producao = st.number_input("Produção", min_value=0)
        perdas = st.number_input("Perdas", min_value=0)
        quarentena = st.number_input("Quarentena", min_value=0)
        submit = st.form_submit_button("Registrar")

        if submit:
            novo = pd.DataFrame([[data.strftime("%d/%m/%Y"), operador, codigo, ml, producao, perdas, quarentena]],
                                columns=['Data', 'Operador', 'Código', 'ML', 'Produção', 'Perdas', 'Quarentena'])
            novo.to_csv(SAIDA_CSV, mode='a', header=False, index=False)
            st.success("✅ Saída registrada com sucesso!")

# CONSULTAR SALDO
elif opcao == "Consultar Saldo":
    st.header("📊 Saldo Atual de Vasilhames")
    entradas = pd.read_csv(ENTRADA_CSV)
    saidas = pd.read_csv(SAIDA_CSV)

    saldo = {}

    for _, row in entradas.iterrows():
        chave = (row['Código'], row['ML'])
        saldo[chave] = saldo.get(chave, 0) + int(row['Quantidade'])

    for _, row in saidas.iterrows():
        chave = (row['Código'], row['ML'])
        total_saida = int(row['Produção']) + \
            int(row['Perdas']) + int(row['Quarentena'])
        saldo[chave] = saldo.get(chave, 0) - total_saida

    resultado = []
    for (codigo, ml), total in saldo.items():
        resultado.append({'Código': codigo, 'ML': ml, 'Saldo': total})

    st.dataframe(pd.DataFrame(resultado))

# ENVIAR POR E-MAIL
elif opcao == "Enviar por E-mail":
    st.header("📧 Enviar Saldo por E-mail")
    destino = st.text_input("E-mail de destino")
    enviar = st.button("Enviar Relatório")

    if enviar:
        entradas = pd.read_csv(ENTRADA_CSV)
        saidas = pd.read_csv(SAIDA_CSV)

        saldo = {}
        for _, row in entradas.iterrows():
            chave = (row['Código'], row['ML'])
            saldo[chave] = saldo.get(chave, 0) + int(row['Quantidade'])

        for _, row in saidas.iterrows():
            chave = (row['Código'], row['ML'])
            total_saida = int(row['Produção']) + \
                int(row['Perdas']) + int(row['Quarentena'])
            saldo[chave] = saldo.get(chave, 0) - total_saida

        mensagem = "Relatório de Saldo de Vasilhames\n\n"
        for (codigo, ml), total in saldo.items():
            mensagem += f"Código: {codigo} | ML: {ml} => Saldo: {total}\n"

        msg = EmailMessage()
        msg.set_content(mensagem)
        msg['Subject'] = 'Relatório de Saldo - Vasilhames'
        msg['From'] = "programandocomedgar@gmail.com"
        msg['To'] = destino

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login("programandocomedgar@gmail.com",
                           "kqcy nzai axex ylcr")
                smtp.send_message(msg)
            st.success("✅ E-mail enviado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao enviar e-mail: {e}")
