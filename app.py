import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Configuração da senha de administrador (apenas um valor fixo)
ADMIN_PASSWORD = "admin123"  # você pode mudar para o que quiser

# Cria pasta data
os.makedirs("data", exist_ok=True)
ENTRADA_CSV = "data/entrada_vasilhames.csv"
SAIDA_CSV = "data/saida_vasilhames.csv"

def inicializar_arquivos():
    if not os.path.exists(ENTRADA_CSV):
        pd.DataFrame(columns=['Data', 'Turno', 'Operador', 'Máquina', 'Código',
                              'ML', 'Cor', 'Gr', 'Quantidade', 'Tipo']).to_csv(ENTRADA_CSV, index=False)
    if not os.path.exists(SAIDA_CSV):
        pd.DataFrame(columns=['Data', 'Operador', 'Código', 'ML', 'Retirada',
                              'Perdas', 'Quarentena']).to_csv(SAIDA_CSV, index=False)

inicializar_arquivos()

st.sidebar.title("📦 Controle de Vasilhames - Sopro")
menu = st.sidebar.radio("Menu:", [
    "Registrar Entrada",
    "Registrar Saída",
    "Consultar Saldo",
    "Enviar por E‑mail",
    "Corrigir/Excluir"
])

if menu == "Corrigir/Excluir":
    senha = st.text_input("Senha de administrador", type="password")
    if senha != ADMIN_PASSWORD:
        st.error("🔒 Senha incorreta ou acesso negado.")
        st.stop()
    st.success("🔓 Acesso liberado")

    st.header("📋 Corrigir ou Excluir entradas")

    df_e = pd.read_csv(ENTRADA_CSV)
    df_s = pd.read_csv(SAIDA_CSV)

    tipo = st.radio("Selecione o tipo", ["Entrada", "Saída"])
    if tipo == "Entrada":
        df = df_e
    else:
        df = df_s

    st.dataframe(df)

    idx = st.number_input("Digite o índice da linha", min_value=0, max_value=len(df)-1, step=1)
    campo = st.selectbox("Campo", df.columns)
    acao = st.radio("Ação", ["Editar valor", "Excluir linha"])

    if acao == "Editar valor":
        novo = st.text_input("Novo valor", value=str(df.at[idx, campo]))
        if st.button("Salvar alteração"):
            df.at[idx, campo] = novo
            df.to_csv(ENTRADA_CSV if tipo=="Entrada" else SAIDA_CSV, index=False)
            st.success("📝 Valor atualizado com sucesso!")
            st.experimental_rerun()
    else:
        if st.button("Excluir esta linha"):
            df = df.drop(idx).reset_index(drop=True)
            df.to_csv(ENTRADA_CSV if tipo=="Entrada" else SAIDA_CSV, index=False)
            st.success("❌ Linha excluída com sucesso!")
            st.experimental_rerun()

elif menu == "Registrar Entrada":
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
        submit = st.form_submit_button("Registrar")
        if submit:
            novo = pd.DataFrame([[data.strftime("%d/%m/%Y"), turno, operador, maquina, codigo, ml, cor, gr, quantidade, "Entrada"]],
                                columns=['Data', 'Turno', 'Operador', 'Máquina', 'Código', 'ML', 'Cor', 'Gr', 'Quantidade', 'Tipo'])
            novo.to_csv(ENTRADA_CSV, mode='a', header=False, index=False)
            st.success("✅ Entrada registrada com sucesso!")

elif menu == "Registrar Saída":
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

elif menu == "Consultar Saldo":
    st.header("📊 Saldo Atual de Vasilhames")
    if os.path.exists(ENTRADA_CSV) and os.path.exists(SAIDA_CSV):
        entradas = pd.read_csv(ENTRADA_CSV)
        saidas = pd.read_csv(SAIDA_CSV)
        saldo = {}
        for _, r in entradas.iterrows():
            chave = (r['Código'], r['ML'])
            saldo[chave] = saldo.get(chave, 0) + int(r['Quantidade'])
        for _, r in saidas.iterrows():
            chave = (r['Código'], r['ML'])
            total = int(r['Produção']) + int(r['Perdas']) + int(r['Quarentena'])
            saldo[chave] = saldo.get(chave, 0) - total
        resultado = [{'Código': c, 'ML': ml, 'Saldo': s} for (c, ml), s in saldo.items()]
        st.dataframe(pd.DataFrame(resultado))
    else:
        st.warning("⚠️ Nenhum registro encontrado.")

elif menu == "Enviar por E‑mail":
    st.header("📧 Enviar Saldo por E‑mail")
    destino = st.text_input("E‑mail de destino")
    if st.button("Enviar Relatório"):
        if os.path.exists(ENTRADA_CSV) and os.path.exists(SAIDA_CSV):
            entradas = pd.read_csv(ENTRADA_CSV)
            saidas = pd.read_csv(SAIDA_CSV)
            saldo = {}
            for _, r in entradas.iterrows():
                chave = (r['Código'], r['ML'])
                saldo[chave] = saldo.get(chave, 0) + int(r['Quantidade'])
            for _, r in saidas.iterrows():
                chave = (r['Código'], r['ML'])
                total = int(r['Produção']) + int(r['Perdas']) + int(r['Quarentena'])
                saldo[chave] = saldo.get(chave, 0) - total
            mensagem = "Relatório de Saldo de Vasilhames\n\n"
            for (c, ml), s in saldo.items():
                mensagem += f"Código: {c} | ML: {ml} => Saldo: {s}\n"
            msg = EmailMessage()
            msg.set_content(mensagem)
            msg['Subject'] = 'Relatório de Saldo - Vasilhames'
            msg['From'] = "programandocomedgar@gmail.com"
            msg['To'] = destino
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login("programandocomedgar@gmail.com", "kqcy nzai axex ylcr")
                    smtp.send_message(msg)
                st.success("✅ E-mail enviado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao enviar e-mail: {e}")
        else:
            st.warning("⚠️ Os arquivos ainda não existem.")

