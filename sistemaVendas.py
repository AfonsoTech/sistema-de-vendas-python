#Configuração inicial: importações e configuração do banco de dados
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

conexao = sqlite3.connect("sistema_vendas.db")
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto TEXT,
    quantidade INTEGER,
    preco REAL,
    total REAL,
    data TEXT
)
""")
conexao.commit()

#Funcionalidade: funções de atualização de tabelas de produtos e vendas
def atualizar_produtos():
    tabela_produtos.delete(*tabela_produtos.get_children())
    cursor.execute("SELECT * FROM produtos")
    dados = cursor.fetchall()
    for linha in dados:
        tabela_produtos.insert("", tk.END, values=linha)
    carregar_combobox()

def atualizar_vendas():
    tabela_vendas.delete(*tabela_vendas.get_children())
    cursor.execute("SELECT * FROM vendas")
    dados = cursor.fetchall()
    for linha in dados:
        tabela_vendas.insert("", tk.END, values=linha)

def carregar_combobox():
    cursor.execute("SELECT nome FROM produtos")
    produtos = cursor.fetchall()
    lista = []
    for produto in produtos:
        lista.append(produto[0])
    combo_produto["values"] = lista

# Funcionalidade: adicionar lógica de registro de produto
def cadastrar_produto():
    nome = entry_nome.get()
    preco = entry_preco.get()
    estoque = entry_estoque.get()
    if nome == "" or preco == "" or estoque == "":
        messagebox.showerror("Erro", "Preencha todos os campos")
        return
    try:
        preco = float(preco)
        estoque = int(estoque)
        cursor.execute("""
            INSERT INTO produtos(nome, preco, estoque)
            VALUES (?, ?, ?)
        """, (nome, preco, estoque))
        conexao.commit()
        messagebox.showinfo("Sucesso", "Produto cadastrado")
        entry_nome.delete(0, tk.END)
        entry_preco.delete(0, tk.END)
        entry_estoque.delete(0, tk.END)
        atualizar_produtos()
    except:
        messagebox.showerror("Erro", "Digite valores válidos")

#Funcionalidade: adicionar lógica de registro de vendas
def registrar_venda():
    produto = combo_produto.get()
    quantidade = entry_quantidade.get()
    if produto == "" or quantidade == "":
        messagebox.showerror("Erro", "Preencha os campos")
        return
    try:
        quantidade = int(quantidade)
        cursor.execute("""
            SELECT preco, estoque FROM produtos WHERE nome = ?
        """, (produto,))
        resultado = cursor.fetchone()
        if resultado is None:
            messagebox.showerror("Erro", "Produto não encontrado")
            return
        preco = resultado[0]
        estoque = resultado[1]
        if quantidade > estoque:
            messagebox.showerror("Erro", "Estoque insuficiente")
            return
        total = preco * quantidade
        data = datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute("""
            INSERT INTO vendas(produto, quantidade, preco, total, data)
            VALUES (?, ?, ?, ?, ?)
        """, (produto, quantidade, preco, total, data))
        novo_estoque = estoque - quantidade
        cursor.execute("""
            UPDATE produtos SET estoque = ? WHERE nome = ?
        """, (novo_estoque, produto))
        conexao.commit()
        messagebox.showinfo("Sucesso", "Venda registrada")
        atualizar_produtos()
        atualizar_vendas()
        atualizar_estatisticas()
        entry_quantidade.delete(0, tk.END)
    except:
        messagebox.showerror("Erro", "Digite uma quantidade válida")

#Características: estatísticas, relatório e gráfico do Pandas
def atualizar_estatisticas():
    cursor.execute("SELECT total FROM vendas")
    dados = cursor.fetchall()
    if len(dados) == 0:
        label_estatisticas.config(text="Nenhuma venda registrada")
        return
    valores = np.array([item[0] for item in dados])
    soma = np.sum(valores)
    media = np.mean(valores)
    maior = np.max(valores)
    menor = np.min(valores)
    texto = f"""
Total Vendido: R$ {soma:.2f}
Média das Vendas: R$ {media:.2f}
Maior Venda: R$ {maior:.2f}
Menor Venda: R$ {menor:.2f}
Quantidade de Vendas: {len(valores)}
"""
    label_estatisticas.config(text=texto)

def relatorio_pandas():
    df = pd.read_sql_query("SELECT * FROM vendas", conexao)
    if df.empty:
        messagebox.showwarning("Aviso", "Nenhuma venda cadastrada")
        return
    resumo = df.groupby("produto")["total"].sum()
    print("\nRELATÓRIO DE VENDAS\n")
    print(resumo)
    messagebox.showinfo("Relatório", "Relatório gerado no terminal")

def gerar_grafico():
    df = pd.read_sql_query("SELECT * FROM vendas", conexao)
    if df.empty:
        messagebox.showwarning("Aviso", "Nenhuma venda cadastrada")
        return
    agrupado = df.groupby("produto")["total"].sum()
    janela_grafico = tk.Toplevel()
    janela_grafico.title("Gráfico de Vendas")
    janela_grafico.geometry("700x500")
    figura, ax = plt.subplots(figsize=(7, 5))
    agrupado.plot(kind="bar", ax=ax)
    ax.set_title("Vendas por Produto")
    ax.set_xlabel("Produtos")
    ax.set_ylabel("Valor Total")
    canvas = FigureCanvasTkAgg(figura, master=janela_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)