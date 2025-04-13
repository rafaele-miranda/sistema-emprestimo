import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tkinter import filedialog


class SistemaEmprestimo:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Empréstimo de Equipamentos")
        self.root.geometry("1200x700")
        
        # Configuração do tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Conexão com o banco de dados PRIMEIRO
        self.conectar_banco_dados()
        
        # Depois criar widgets e atualizar comboboxes
        self.criar_widgets()
        self.atualizar_todos_comboboxes()
        self.atualizar_lista_equipamentos()
        
    def atualizar_todos_comboboxes(self):
        """Atualiza todos os comboboxes do sistema"""
        try:
            # Carrega dados do banco
            usuarios = self.carregar_usuarios()
            equipamentos = self.carregar_equipamentos()
            emprestimos_ativos = self.carregar_emprestimos_ativos()
            
            # Atualiza combobox de usuários
            if hasattr(self, 'combo_usuario'):
                self.combo_usuario.configure(values=usuarios)
            
            if hasattr(self, 'combo_usuario_devolucao_massa'):
                self.combo_usuario_devolucao_massa.configure(values=usuarios)
            
            # Atualiza combobox de equipamentos
            if hasattr(self, 'combo_equipamento'):
                self.combo_equipamento.configure(values=equipamentos)
            
            # Verifica se o combobox de empréstimos existe
            if hasattr(self, 'lista_emprestimos_devolucao'):
                self.lista_emprestimos_devolucao.configure(values=emprestimos_ativos)
            
            # Atualiza especificamente os comboboxes da aba de troca
            if hasattr(self, 'combo_emprestimo_troca'):
                self.atualizar_comboboxes_troca()
                
        except Exception as e:
            print(f"Erro ao atualizar comboboxes: {e}")
        
    def conectar_banco_dados(self):
        self.conn = sqlite3.connect('emprestimos.db')
        self.cursor = self.conn.cursor()
        
        # Criar tabelas se não existirem (com as novas modificações)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            quantidade INTEGER DEFAULT 1
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS unidades_equipamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento_id INTEGER,
            codigo TEXT UNIQUE,
            disponivel INTEGER DEFAULT 1,
            FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE,
            email TEXT
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            usuario_id INTEGER,
            data_emprestimo TEXT,
            data_devolucao_prevista TEXT,
            data_devolucao_real TEXT,
            FOREIGN KEY (unidade_id) REFERENCES unidades_equipamento(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS trocas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emprestimo_id INTEGER,
            unidade_antiga_id INTEGER,
            unidade_nova_id INTEGER,
            data_troca TEXT,
            motivo TEXT,
            FOREIGN KEY (emprestimo_id) REFERENCES emprestimos(id),
            FOREIGN KEY (unidade_antiga_id) REFERENCES unidades_equipamento(id),
            FOREIGN KEY (unidade_nova_id) REFERENCES unidades_equipamento(id)
        )
        ''')
        self.conn.commit()
    
    def criar_widgets(self):
        # Frame principal
        self.frame_principal = ctk.CTkFrame(self.root)
        self.frame_principal.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Abas
        self.abas = ctk.CTkTabview(self.frame_principal)
        self.abas.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Adicionar abas
        self.aba_emprestimo = self.abas.add("Empréstimo")
        self.aba_devolucao = self.abas.add("Devolução")
        self.aba_troca = self.abas.add("Troca")
        self.aba_cadastro = self.abas.add("Cadastros")
        self.aba_relatorios = self.abas.add("Relatórios")
        
        # Widgets das abas
        self.criar_aba_emprestimo()
        self.criar_aba_devolucao()
        self.criar_aba_troca()
        self.criar_aba_cadastro()
        self.criar_aba_relatorios()
    
    def criar_aba_emprestimo(self):
        frame = ctk.CTkFrame(self.aba_emprestimo)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Registrar Empréstimo em Massa", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Selecionar usuário
        ctk.CTkLabel(frame, text="Selecione o usuário:").pack()
        self.combo_usuario = ctk.CTkComboBox(frame, values=self.carregar_usuarios())
        self.combo_usuario.pack(pady=5)
        
        # Selecionar equipamento
        ctk.CTkLabel(frame, text="Selecione o equipamento:").pack()
        self.combo_equipamento = ctk.CTkComboBox(frame)
        self.combo_equipamento.configure(values=self.carregar_equipamentos())
        self.combo_equipamento.pack(pady=5)
        
        # Quantidade a emprestar
        ctk.CTkLabel(frame, text="Quantidade a emprestar:").pack()
        self.entry_quantidade = ctk.CTkEntry(frame)
        self.entry_quantidade.pack(pady=5)
        
        # Data de devolução
        ctk.CTkLabel(frame, text="Data de devolução prevista:").pack()
        self.data_devolucao_massa = ctk.CTkEntry(frame)
        self.data_devolucao_massa.insert(0, (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y"))
        self.data_devolucao_massa.pack(pady=5)
        
        # Botão para verificar disponibilidade
        btn_verificar = ctk.CTkButton(frame, text="Verificar Disponibilidade", command=self.verificar_disponibilidade)
        btn_verificar.pack(pady=10)
        
        # Área para mostrar unidades disponíveis
        self.label_disponiveis = ctk.CTkLabel(frame, text="")
        self.label_disponiveis.pack(pady=5)
        
        # Botão registrar empréstimo em massa
        btn_emprestar_massa = ctk.CTkButton(frame, text="Registrar Empréstimo em Massa", command=self.registrar_emprestimo_massa)
        btn_emprestar_massa.pack(pady=20)
        
    def verificar_disponibilidade(self):
        equipamento = self.combo_equipamento.get()  # Corrigido de combo_equipamento_massa para combo_equipamento
        quantidade = self.entry_quantidade.get()
        
        if not equipamento or not quantidade:
            messagebox.showerror("Erro", "Selecione um equipamento e informe a quantidade!")
            return
        
        try:
            quantidade = int(quantidade)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            return
        
        # Verificar unidades disponíveis
        self.cursor.execute('''
        SELECT COUNT(*) 
        FROM unidades_equipamento ue
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE e.nome = ? AND ue.disponivel = 1
        ''', (equipamento,))
        disponiveis = self.cursor.fetchone()[0]
        
        if disponiveis < quantidade:
            self.label_disponiveis.configure(
                text=f"Aviso: Só há {disponiveis} unidades disponíveis (você solicitou {quantidade})",
                text_color="orange"
            )
        else:
            self.label_disponiveis.configure(
                text=f"Disponibilidade confirmada: {quantidade} unidades disponíveis",
                text_color="green"
            )
        
        self.unidades_a_emprestar = quantidade

    def registrar_emprestimo_massa(self):
        usuario = self.combo_usuario.get()
        equipamento = self.combo_equipamento.get()  # Corrigido de combo_equipamento_massa para combo_equipamento
        data_devolucao = self.data_devolucao_massa.get()
        
        if not hasattr(self, 'unidades_a_emprestar') or self.unidades_a_emprestar <= 0:
            messagebox.showerror("Erro", "Verifique a disponibilidade primeiro!")
            return
        
        try:
            data_devolucao = datetime.strptime(data_devolucao, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido! Use DD/MM/AAAA")
            return
        
        # Extrair ID do usuário
        matricula = usuario.split(" - ")[1]
        self.cursor.execute("SELECT id FROM usuarios WHERE matricula = ?", (matricula,))
        usuario_id = self.cursor.fetchone()[0]
        
        # Obter unidades disponíveis
        self.cursor.execute('''
        SELECT ue.id 
        FROM unidades_equipamento ue
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE e.nome = ? AND ue.disponivel = 1
        LIMIT ?
        ''', (equipamento, self.unidades_a_emprestar))
        
        unidades_ids = [row[0] for row in self.cursor.fetchall()]
        
        if len(unidades_ids) < self.unidades_a_emprestar:
            messagebox.showerror("Erro", f"Só há {len(unidades_ids)} unidades disponíveis (você solicitou {self.unidades_a_emprestar})")
            return
        
        # Registrar todos os empréstimos
        data_emprestimo = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            for unidade_id in unidades_ids:
                self.cursor.execute('''
                INSERT INTO emprestimos (unidade_id, usuario_id, data_emprestimo, data_devolucao_prevista)
                VALUES (?, ?, ?, ?)
                ''', (unidade_id, usuario_id, data_emprestimo, data_devolucao))
                
                self.cursor.execute("UPDATE unidades_equipamento SET disponivel = 0 WHERE id = ?", (unidade_id,))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"{len(unidades_ids)} unidades emprestadas com sucesso para {usuario.split(' - ')[0]}!")
            
            # Atualizar a interface
            self.label_disponiveis.configure(text="")
            self.entry_quantidade.delete(0, "end")
            self.lista_emprestimos_devolucao.configure(values=self.carregar_emprestimos_ativos())
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao registrar empréstimos: {str(e)}")
    
    def criar_aba_devolucao(self):
        frame = ctk.CTkFrame(self.aba_devolucao)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Abas para devolução (individual e em massa)
        tabview = ctk.CTkTabview(frame)
        tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Aba de devolução individual
        tab_individual = tabview.add("Individual")
        self.criar_aba_devolucao_individual(tab_individual)
        
        # Aba de devolução em massa
        tab_massa = tabview.add("Em Massa")
        self.criar_aba_devolucao_massa(tab_massa)

    def criar_aba_devolucao_individual(self, frame):
        ctk.CTkLabel(frame, text="Devolução Individual", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Lista de empréstimos ativos
        ctk.CTkLabel(frame, text="Selecione o empréstimo:").pack()
        self.lista_emprestimos_devolucao = ctk.CTkComboBox(frame, values=self.carregar_emprestimos_ativos())
        self.lista_emprestimos_devolucao.pack(pady=5)
        
        # Botão registrar devolução
        btn_devolver = ctk.CTkButton(frame, text="Registrar Devolução", command=self.registrar_devolucao)
        btn_devolver.pack(pady=20)
        
    def carregar_emprestimos_usuario(self):
        # Inicializa o dicionário se não existir
        if not hasattr(self, 'checkboxes_devolucao_massa'):
            self.checkboxes_devolucao_massa = {}
        else:
            # Limpa o dicionário existente
            self.checkboxes_devolucao_massa.clear()
    
    # Restante da função...
        # Limpa o frame de lista
        for widget in self.frame_lista_devolucao_massa.winfo_children():
            widget.destroy()
        
        usuario = self.combo_usuario_devolucao_massa.get()
        if not usuario:
            messagebox.showwarning("Aviso", "Selecione um usuário primeiro!")
            return
        
        # Extrai a matrícula do usuário
        matricula = usuario.split(" - ")[1]
        
        # Busca os empréstimos ativos do usuário
        self.cursor.execute('''
        SELECT emp.id, e.nome, ue.codigo, emp.data_emprestimo, emp.data_devolucao_prevista
        FROM emprestimos emp
        JOIN usuarios u ON emp.usuario_id = u.id
        JOIN unidades_equipamento ue ON emp.unidade_id = ue.id
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE u.matricula = ? AND emp.data_devolucao_real IS NULL
        ''', (matricula,))
        
        emprestimos = self.cursor.fetchall()
        
        if not emprestimos:
            ctk.CTkLabel(self.frame_lista_devolucao_massa, 
                        text="Nenhum empréstimo ativo para este usuário.").pack()
            return
        
        # Dicionário para armazenar os checkboxes
        self.checkboxes_devolucao_massa = {}
        
        for emp in emprestimos:
            frame_item = ctk.CTkFrame(self.frame_lista_devolucao_massa)
            frame_item.pack(fill="x", pady=2)
            
            # Checkbox
            var = ctk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(frame_item, text="", variable=var)
            checkbox.pack(side="left", padx=5)
            self.checkboxes_devolucao_massa[emp[0]] = var
            
            # Detalhes do empréstimo
            texto = f"{emp[1]} (Unidade: {emp[2]}) - Emprestado em: {emp[3]} - Devolução prevista: {emp[4]}"
            label = ctk.CTkLabel(frame_item, text=texto)
            label.pack(side="left", fill="x", expand=True)
            
    def registrar_devolucao_massa(self):
        if not hasattr(self, 'checkboxes_devolucao_massa') or not self.checkboxes_devolucao_massa:
            messagebox.showwarning("Aviso", "Nenhum empréstimo carregado para devolução!")
            return
        
        # Filtra apenas os empréstimos marcados
        emprestimos_a_devolver = [emp_id for emp_id, var in self.checkboxes_devolucao_massa.items() if var.get()]
        
        if not emprestimos_a_devolver:
            messagebox.showwarning("Aviso", "Selecione pelo menos um item para devolver!")
            return
        
        try:
            data_devolucao = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Inicia transação
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Para cada empréstimo selecionado
            for emp_id in emprestimos_a_devolver:
                # Registrar devolução
                self.cursor.execute('''
                UPDATE emprestimos SET data_devolucao_real = ? 
                WHERE id = ? AND data_devolucao_real IS NULL
                ''', (data_devolucao, emp_id))
                
                if self.cursor.rowcount == 0:
                    raise Exception(f"Empréstimo {emp_id} já devolvido ou não encontrado")
                
                # Liberar unidade
                self.cursor.execute('''
                UPDATE unidades_equipamento SET disponivel = 1 
                WHERE id = (SELECT unidade_id FROM emprestimos WHERE id = ?)
                ''', (emp_id,))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"{len(emprestimos_a_devolver)} itens devolvidos com sucesso!")
        
            # Atualiza a interface
            self.carregar_emprestimos_usuario()  # Recarrega a lista (que agora estará vazia se todos foram devolvidos)
            self.atualizar_todos_comboboxes()
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao registrar devoluções: {str(e)}")

    def criar_aba_devolucao_massa(self, frame):
        ctk.CTkLabel(frame, text="Devolução em Massa", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Selecionar usuário
        ctk.CTkLabel(frame, text="Selecione o usuário:").pack()
        self.combo_usuario_devolucao_massa = ctk.CTkComboBox(frame, values=self.carregar_usuarios())
        self.combo_usuario_devolucao_massa.pack(pady=5)
        
        # Botão para carregar empréstimos do usuário
        btn_carregar = ctk.CTkButton(frame, text="Carregar Empréstimos", command=self.carregar_emprestimos_usuario)
        btn_carregar.pack(pady=10)
        
        # Lista de empréstimos do usuário (com checkboxes)
        ctk.CTkLabel(frame, text="Selecione os itens para devolver:").pack()
        self.frame_lista_devolucao_massa = ctk.CTkScrollableFrame(frame, height=200)
        self.frame_lista_devolucao_massa.pack(pady=10, fill="both", expand=True)
        
        # Botão para devolver todos os selecionados
        btn_devolver_massa = ctk.CTkButton(frame, text="Devolver Itens Selecionados", command=self.registrar_devolucao_massa)
        btn_devolver_massa.pack(pady=20)
        
    def atualizar_unidades_troca(self, event=None):
        """Atualiza o combobox de unidades quando um equipamento é selecionado"""
        try:
            equipamento = self.combo_equipamento_troca.get()
            
            if not equipamento:
                self.combo_unidade_troca.configure(values=[])
                return
                
            unidades = self.carregar_unidades_disponiveis(equipamento)
            
            # Atualiza o combobox
            self.combo_unidade_troca.configure(values=unidades)
            
            if unidades:
                self.combo_unidade_troca.set(unidades[0])
            else:
                self.combo_unidade_troca.set("")
                messagebox.showwarning("Aviso", f"Nenhuma unidade disponível para {equipamento}")
                
        except Exception as e:
            print(f"Erro ao atualizar unidades: {e}")
            self.combo_unidade_troca.set("")
        
    def atualizar_comboboxes_troca(self):
        try:
            print("\nAtualizando comboboxes de troca...")
            
            # Empréstimos ativos
            emprestimos_ativos = self.carregar_emprestimos_ativos()
            print(f"Empréstimos ativos encontrados: {len(emprestimos_ativos)}")
            self.combo_emprestimo_troca.configure(values=emprestimos_ativos)
            
            # Equipamentos
            equipamentos = self.carregar_equipamentos()
            print(f"Equipamentos encontrados: {len(equipamentos)}")
            self.combo_equipamento_troca.configure(values=equipamentos)
            
            # Unidades (se já houver seleção)
            if self.combo_equipamento_troca.get():
                self.atualizar_unidades_troca()
            
        except Exception as e:
            print(f"Erro ao atualizar comboboxes de troca: {e}")
        
    def criar_aba_troca(self):
        frame = ctk.CTkFrame(self.aba_troca)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Registrar Troca de Equipamento", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Empréstimo para troca
        ctk.CTkLabel(frame, text="Selecione o empréstimo:").pack()
        self.combo_emprestimo_troca = ctk.CTkComboBox(frame, state="readonly")
        self.combo_emprestimo_troca.pack(pady=5)
        
        # Novo equipamento
        ctk.CTkLabel(frame, text="Novo equipamento:").pack()
        self.combo_equipamento_troca = ctk.CTkComboBox(frame, state="readonly", command=self.atualizar_unidades_troca)
        self.combo_equipamento_troca.pack(pady=5)
        
        # Nova unidade
        ctk.CTkLabel(frame, text="Nova unidade:").pack()
        self.combo_unidade_troca = ctk.CTkComboBox(frame, state="readonly")
        self.combo_unidade_troca.pack(pady=5)
        
        # Motivo da troca
        ctk.CTkLabel(frame, text="Motivo da troca:").pack()
        self.entry_motivo_troca = ctk.CTkEntry(frame)
        self.entry_motivo_troca.pack(pady=5)
        
        # Botão registrar troca
        btn_troca = ctk.CTkButton(frame, text="Registrar Troca", command=self.registrar_troca)
        btn_troca.pack(pady=20)
        
        # Atualizar comboboxes
        self.atualizar_comboboxes_troca()
    
    def criar_aba_cadastro(self):
        notebook = ctk.CTkTabview(self.aba_cadastro)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Abas de cadastro
        tab_equip = notebook.add("Equipamentos")
        tab_unidades = notebook.add("Unidades")
        tab_user = notebook.add("Usuários")
        
        # Widgets das abas de cadastro
        self.criar_aba_cadastro_equipamentos(tab_equip)
        self.criar_aba_cadastro_unidades(tab_unidades)
        self.criar_aba_cadastro_usuarios(tab_user)
    
    def criar_aba_cadastro_equipamentos(self, frame):
        ctk.CTkLabel(frame, text="Cadastro de Equipamentos", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Nome do equipamento
        ctk.CTkLabel(frame, text="Nome:").pack()
        self.entry_nome_equip = ctk.CTkEntry(frame)
        self.entry_nome_equip.pack(pady=5)
        
        # Descrição
        ctk.CTkLabel(frame, text="Descrição:").pack()
        self.entry_desc_equip = ctk.CTkEntry(frame)
        self.entry_desc_equip.pack(pady=5)
        
        # Quantidade
        ctk.CTkLabel(frame, text="Quantidade:").pack()
        self.entry_quant_equip = ctk.CTkEntry(frame)
        self.entry_quant_equip.insert(0, "1")
        self.entry_quant_equip.pack(pady=5)
        
        # Botão cadastrar
        btn_cadastrar = ctk.CTkButton(frame, text="Cadastrar Equipamento", command=self.cadastrar_equipamento)
        btn_cadastrar.pack(pady=20)
        
        # Lista de equipamentos
        ctk.CTkLabel(frame, text="Equipamentos cadastrados:").pack()
        self.lista_equipamentos = ctk.CTkTextbox(frame, height=150)
        self.lista_equipamentos.pack(pady=10, fill="x")
        self.atualizar_lista_equipamentos()
    
    def criar_aba_cadastro_unidades(self, frame):
        ctk.CTkLabel(frame, text="Cadastro de Unidades", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Selecionar equipamento
        ctk.CTkLabel(frame, text="Equipamento:").pack()
        self.combo_equip_unidade = ctk.CTkComboBox(frame, values=self.carregar_equipamentos())
        self.combo_equip_unidade.pack(pady=5)
        
        # Código da unidade
        ctk.CTkLabel(frame, text="Código da unidade:").pack()
        self.entry_codigo_unidade = ctk.CTkEntry(frame)
        self.entry_codigo_unidade.pack(pady=5)
        
        # Botão cadastrar
        btn_cadastrar = ctk.CTkButton(frame, text="Cadastrar Unidade", command=self.cadastrar_unidade)
        btn_cadastrar.pack(pady=20)
        
        # Lista de unidades
        ctk.CTkLabel(frame, text="Unidades cadastradas:").pack()
        self.lista_unidades = ctk.CTkTextbox(frame, height=150)
        self.lista_unidades.pack(pady=10, fill="x")
        self.atualizar_lista_unidades()
    
    def criar_aba_cadastro_usuarios(self, frame):
        ctk.CTkLabel(frame, text="Cadastro de Usuários", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Nome do usuário
        ctk.CTkLabel(frame, text="Nome:").pack()
        self.entry_nome_user = ctk.CTkEntry(frame)
        self.entry_nome_user.pack(pady=5)
        
        # Matrícula
        ctk.CTkLabel(frame, text="Matrícula:").pack()
        self.entry_matricula = ctk.CTkEntry(frame)
        self.entry_matricula.pack(pady=5)
        
        # Email
        ctk.CTkLabel(frame, text="Email:").pack()
        self.entry_email = ctk.CTkEntry(frame)
        self.entry_email.pack(pady=5)
        
        # Botão cadastrar
        btn_cadastrar = ctk.CTkButton(frame, text="Cadastrar Usuário", command=self.cadastrar_usuario)
        btn_cadastrar.pack(pady=20)
        
        # Lista de usuários
        ctk.CTkLabel(frame, text="Usuários cadastrados:").pack()
        self.lista_usuarios = ctk.CTkTextbox(frame, height=150)
        self.lista_usuarios.pack(pady=10, fill="x")
        self.atualizar_lista_usuarios()
    
    def criar_aba_relatorios(self):
        frame = ctk.CTkFrame(self.aba_relatorios)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Relatórios", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Botões de relatórios
        btn_emprestimos_ativos = ctk.CTkButton(frame, text="Empréstimos Ativos", command=self.mostrar_emprestimos_ativos)
        btn_emprestimos_ativos.pack(pady=10, fill="x")
        
        btn_historico = ctk.CTkButton(frame, text="Histórico Completo", command=self.mostrar_historico_completo)
        btn_historico.pack(pady=10, fill="x")
        
        btn_atrasados = ctk.CTkButton(frame, text="Equipamentos Atrasados", command=self.mostrar_atrasados)
        btn_atrasados.pack(pady=10, fill="x")
        
        btn_trocas = ctk.CTkButton(frame, text="Histórico de Trocas", command=self.mostrar_trocas)
        btn_trocas.pack(pady=10, fill="x")
        
        btn_exportar_pdf = ctk.CTkButton(frame, text="Exportar Relatório em PDF", command=self.exportar_relatorio_pdf)
        btn_exportar_pdf.pack(pady=10, fill="x")

        
        # Área de exibição dos relatórios
        self.area_relatorio = ctk.CTkTextbox(frame, height=300)
        self.area_relatorio.pack(pady=20, fill="both", expand=True)
    
    # Métodos auxiliares
    def carregar_usuarios(self):
        self.cursor.execute("SELECT nome || ' - ' || matricula FROM usuarios")
        return [row[0] for row in self.cursor.fetchall()]
    
    def carregar_equipamentos(self):
        try:
            self.cursor.execute("SELECT nome FROM equipamentos")
            equipamentos = [row[0] for row in self.cursor.fetchall()]
            print("Equipamentos encontrados:", equipamentos)  # Debug
            return equipamentos
        except Exception as e:
            print("Erro ao carregar equipamentos:", e)  # Debug
            return []
    
    def carregar_unidades_disponiveis(self, equipamento_nome):
        """Carrega unidades disponíveis para um equipamento específico"""
        try:
            self.cursor.execute('''
            SELECT ue.codigo 
            FROM unidades_equipamento ue
            JOIN equipamentos e ON ue.equipamento_id = e.id
            WHERE e.nome = ? AND ue.disponivel = 1
            ''', (equipamento_nome,))
            
            unidades = [row[0] for row in self.cursor.fetchall()]
            print(f"Unidades disponíveis para {equipamento_nome}: {unidades}")  # Debug
            return unidades
            
        except Exception as e:
            print(f"Erro ao carregar unidades: {e}")
            return []
    
    
    def atualizar_unidades_disponiveis(self):
        equipamento = self.combo_equipamento.get()
        if equipamento:
            unidades = self.carregar_unidades_disponiveis(equipamento)
            if hasattr(self, 'combo_unidade'):
                self.combo_unidade.configure(values=unidades)
                if unidades:
                    self.combo_unidade.set(unidades[0])
                else:
                    self.combo_unidade.set("")
                    messagebox.showwarning("Aviso", "Nenhuma unidade disponível para este equipamento!")
    

    
    def carregar_emprestimos_ativos(self):
        try:
            self.cursor.execute('''
            SELECT emp.id, u.nome, e.nome, ue.codigo, emp.data_emprestimo, emp.data_devolucao_prevista
            FROM emprestimos emp
            JOIN usuarios u ON emp.usuario_id = u.id
            JOIN unidades_equipamento ue ON emp.unidade_id = ue.id
            JOIN equipamentos e ON ue.equipamento_id = e.id
            WHERE emp.data_devolucao_real IS NULL
            ''')
            resultados = self.cursor.fetchall()
            print("Empréstimos ativos encontrados:", resultados)  # Debug
            return [f"{row[0]} - {row[1]} - {row[2]} (Unidade: {row[3]})" for row in resultados]
        except Exception as e:
            print(f"Erro ao carregar empréstimos ativos: {e}")  # Debug
            return []
    
    # Operações principais
    def registrar_emprestimo(self):
        usuario = self.combo_usuario.get()
        equipamento = self.combo_equipamento.get()
        unidade = self.combo_unidade.get()
        data_devolucao = self.data_devolucao.get()
        
        if not usuario or not equipamento or not unidade:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        try:
            data_devolucao = datetime.strptime(data_devolucao, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido! Use DD/MM/AAAA")
            return
        
        # Extrair ID do usuário
        matricula = usuario.split(" - ")[1]
        self.cursor.execute("SELECT id FROM usuarios WHERE matricula = ?", (matricula,))
        usuario_id = self.cursor.fetchone()[0]
        
        # Extrair ID da unidade
        self.cursor.execute('''
        SELECT ue.id 
        FROM unidades_equipamento ue
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE e.nome = ? AND ue.codigo = ?
        ''', (equipamento, unidade))
        unidade_id = self.cursor.fetchone()[0]
        
        # Registrar empréstimo
        data_emprestimo = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cursor.execute('''
        INSERT INTO emprestimos (unidade_id, usuario_id, data_emprestimo, data_devolucao_prevista)
        VALUES (?, ?, ?, ?)
        ''', (unidade_id, usuario_id, data_emprestimo, data_devolucao))
        
        # Atualizar status da unidade
        self.cursor.execute("UPDATE unidades_equipamento SET disponivel = 0 WHERE id = ?", (unidade_id,))
        
        self.conn.commit()
        messagebox.showinfo("Sucesso", "Empréstimo registrado com sucesso!")
        
        # Atualizar combobox
        self.combo_unidade.configure(values=self.carregar_unidades_disponiveis(equipamento))
        self.lista_emprestimos_devolucao.configure(values=self.carregar_emprestimos_ativos())
        self.combo_emprestimo_troca.configure(values=self.carregar_emprestimos_ativos())
    
    def registrar_devolucao(self):
        emprestimo = self.lista_emprestimos_devolucao.get()
        if not emprestimo:
            messagebox.showerror("Erro", "Selecione um empréstimo!")
            return
        
        try:
        # Modificação aqui - pega apenas o primeiro número antes do primeiro espaço
            emprestimo_id = int(emprestimo.split()[0])
        except (ValueError, IndexError):
            messagebox.showerror("Erro", "Selecione um empréstimo válido!")
            return
        
        data_devolucao = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        try:
            # Obter ID da unidade
            self.cursor.execute("SELECT unidade_id FROM emprestimos WHERE id = ?", (emprestimo_id,))
            unidade_id = self.cursor.fetchone()[0]
            
            # Registrar devolução
            self.cursor.execute('''
            UPDATE emprestimos SET data_devolucao_real = ? 
            WHERE id = ? AND data_devolucao_real IS NULL
            ''', (data_devolucao, emprestimo_id))
            
            if self.cursor.rowcount == 0:
                messagebox.showerror("Erro", "Empréstimo já devolvido ou não encontrado!")
                return
            
            # Liberar unidade
            self.cursor.execute("UPDATE unidades_equipamento SET disponivel = 1 WHERE id = ?", (unidade_id,))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Devolução registrada com sucesso!")
            self.atualizar_todos_comboboxes()

            
            # Atualizar listas
            self.lista_emprestimos_devolucao.configure(values=self.carregar_emprestimos_ativos())
            self.lista_emprestimos_devolucao.set("")
            self.combo_emprestimo_troca.configure(values=self.carregar_emprestimos_ativos())
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao registrar devolução: {str(e)}")
    
    def registrar_troca(self):
        emprestimo = self.combo_emprestimo_troca.get()
        novo_equipamento = self.combo_equipamento_troca.get()
        nova_unidade = self.combo_unidade_troca.get()
        motivo = self.entry_motivo_troca.get()
        
        # Verificação de preenchimento
        if not all([emprestimo, novo_equipamento, nova_unidade]):
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
            return
        
        # Verificação do motivo (opcional)
        if not motivo:
            if not messagebox.askokcancel("Aviso", "Deseja continuar sem informar o motivo da troca?"):
                return

        try:
            # DEBUG: Verificar valores
            print("\n--- DEBUG REGISTRAR TROCA ---")
            print(f"Empréstimo selecionado: {emprestimo}")
            print(f"Novo equipamento: {novo_equipamento}")
            print(f"Nova unidade: {nova_unidade}")
            
            # Extrair ID do empréstimo - versão mais robusta
            try:
                emprestimo_id = int(emprestimo.split()[0])  # Pega o primeiro número do texto
                print(f"ID do empréstimo extraído: {emprestimo_id}")
            except (ValueError, IndexError) as e:
                messagebox.showerror("Erro", f"Formato do empréstimo inválido: {emprestimo}")
                return
            
            # Obter unidade antiga
            self.cursor.execute("SELECT unidade_id FROM emprestimos WHERE id = ?", (emprestimo_id,))
            resultado = self.cursor.fetchone()
            if not resultado:
                messagebox.showerror("Erro", "Empréstimo não encontrado no banco de dados!")
                return
            unidade_antiga_id = resultado[0]
            print(f"Unidade antiga ID: {unidade_antiga_id}")
            
            # Obter nova unidade
            self.cursor.execute('''
            SELECT ue.id 
            FROM unidades_equipamento ue
            JOIN equipamentos e ON ue.equipamento_id = e.id
            WHERE e.nome = ? AND ue.codigo = ? AND ue.disponivel = 1
            ''', (novo_equipamento, nova_unidade))
            resultado = self.cursor.fetchone()
            
            if not resultado:
                messagebox.showerror("Erro", f"Unidade {nova_unidade} não encontrada ou não disponível para {novo_equipamento}!")
                return
                
            unidade_nova_id = resultado[0]
            print(f"Nova unidade ID: {unidade_nova_id}")
            
            # Registrar troca
            data_troca = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.cursor.execute('''
            INSERT INTO trocas (emprestimo_id, unidade_antiga_id, unidade_nova_id, data_troca, motivo)
            VALUES (?, ?, ?, ?, ?)
            ''', (emprestimo_id, unidade_antiga_id, unidade_nova_id, data_troca, motivo))
            
            # Atualizar empréstimo
            self.cursor.execute('''
            UPDATE emprestimos SET unidade_id = ? WHERE id = ?
            ''', (unidade_nova_id, emprestimo_id))
            
            # Atualizar status das unidades
            self.cursor.execute("UPDATE unidades_equipamento SET disponivel = 1 WHERE id = ?", (unidade_antiga_id,))
            self.cursor.execute("UPDATE unidades_equipamento SET disponivel = 0 WHERE id = ?", (unidade_nova_id,))
            
            self.conn.commit()
            print("Troca registrada com sucesso no banco de dados!")
            messagebox.showinfo("Sucesso", "Troca registrada com sucesso!")
            
            # Atualizar interface
            self.atualizar_todos_comboboxes()
            self.combo_emprestimo_troca.set("")
            self.combo_equipamento_troca.set("")
            self.combo_unidade_troca.set("")
            self.entry_motivo_troca.delete(0, "end")
            
        except Exception as e:
            self.conn.rollback()
            print(f"ERRO: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao registrar troca: {str(e)}")
    
    def cadastrar_equipamento(self):
        nome = self.entry_nome_equip.get().strip()  # Remove espaços extras no início/fim
        descricao = self.entry_desc_equip.get().strip()
        quantidade = self.entry_quant_equip.get().strip()
        
        if not nome:
            messagebox.showerror("Erro", "Informe o nome do equipamento!")
            return
        
        try:
            quantidade = int(quantidade) if quantidade else 1
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            return
        
        try:
            # Verificar se equipamento já existe (case insensitive)
            self.cursor.execute('''
            SELECT id FROM equipamentos WHERE LOWER(nome) = LOWER(?)
            ''', (nome,))
            if self.cursor.fetchone() is not None:
                raise sqlite3.IntegrityError("Equipamento com este nome já existe")
            
            # Iniciar transação
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Inserir equipamento
            self.cursor.execute('''
            INSERT INTO equipamentos (nome, descricao, quantidade) 
            VALUES (?, ?, ?)
            ''', (nome, descricao, quantidade))
            
            equipamento_id = self.cursor.lastrowid
            
            # Criar unidades automaticamente se quantidade > 1
            if quantidade > 1:
                for i in range(1, quantidade + 1):
                    codigo = f"{nome[:3].upper()}-{i:03d}"
                    try:
                        self.cursor.execute('''
                        INSERT INTO unidades_equipamento (equipamento_id, codigo) 
                        VALUES (?, ?)
                        ''', (equipamento_id, codigo))
                    except sqlite3.IntegrityError:
                        # Se o código já existir, tentar um padrão diferente
                        codigo = f"{nome[:3].upper()}-{equipamento_id}-{i:03d}"
                        self.cursor.execute('''
                        INSERT INTO unidades_equipamento (equipamento_id, codigo) 
                        VALUES (?, ?)
                        ''', (equipamento_id, codigo))
            
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Equipamento cadastrado com sucesso!")
            
            # Atualiza a interface
            self.atualizar_todos_comboboxes()
            self.atualizar_lista_equipamentos()
            self.atualizar_todos_comboboxes()
            
            # Limpar campos
            self.entry_nome_equip.delete(0, "end")
            self.entry_desc_equip.delete(0, "end")
            self.entry_quant_equip.delete(0, "end")
            self.entry_quant_equip.insert(0, "1")
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                messagebox.showerror("Erro", "Equipamento com este nome já existe!")
            else:
                messagebox.showerror("Erro", f"Erro de integridade: {str(e)}")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao cadastrar equipamento: {str(e)}")
            
    
    def cadastrar_unidade(self):
        equipamento = self.combo_equip_unidade.get()
        codigo = self.entry_codigo_unidade.get()
        
        if not equipamento or not codigo:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        try:
            # Obter ID do equipamento
            self.cursor.execute("SELECT id FROM equipamentos WHERE nome = ?", (equipamento,))
            equipamento_id = self.cursor.fetchone()[0]
            
            # Cadastrar unidade
            self.cursor.execute('''
            INSERT INTO unidades_equipamento (equipamento_id, codigo) VALUES (?, ?)
            ''', (equipamento_id, codigo))
            
            # Atualizar quantidade do equipamento
            self.cursor.execute('''
            UPDATE equipamentos 
            SET quantidade = (SELECT COUNT(*) FROM unidades_equipamento WHERE equipamento_id = ?)
            WHERE id = ?
            ''', (equipamento_id, equipamento_id))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Unidade cadastrada com sucesso!")
            
            self.atualizar_todos_comboboxes()

            
            # Limpar campos
            self.entry_codigo_unidade.delete(0, "end")
            
            # Atualizar listas
            self.atualizar_lista_unidades()
            self.atualizar_unidades_disponiveis()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Código da unidade já existe!")
    
    def cadastrar_usuario(self):
        nome = self.entry_nome_user.get().strip()  # Adicione .strip() para remover espaços extras
        matricula = self.entry_matricula.get().strip()
        email = self.entry_email.get().strip()
        
        # Verificação mais robusta dos campos obrigatórios
        if not nome or not matricula:
            campos_faltando = []
            if not nome:
                campos_faltando.append("nome")
            if not matricula:
                campos_faltando.append("matrícula")
            messagebox.showerror("Erro", f"Informe os seguintes campos: {', '.join(campos_faltando)}")
            return
        
        try:
            # Verifica se a matrícula já existe antes de tentar inserir
            self.cursor.execute("SELECT id FROM usuarios WHERE matricula = ?", (matricula,))
            if self.cursor.fetchone() is not None:
                raise sqlite3.IntegrityError("Matrícula já cadastrada")
            
            # Insere o novo usuário
            self.cursor.execute('''
            INSERT INTO usuarios (nome, matricula, email) VALUES (?, ?, ?)
            ''', (nome, matricula, email))
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
            self.atualizar_todos_comboboxes()
            self.atualizar_lista_usuarios()
            
            # Limpar campos
            self.entry_nome_user.delete(0, "end")
            self.entry_matricula.delete(0, "end")
            self.entry_email.delete(0, "end")
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                messagebox.showerror("Erro", "Matrícula já cadastrada!")
            else:
                messagebox.showerror("Erro", f"Erro de integridade: {str(e)}")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao cadastrar usuário: {str(e)}")
        
    def atualizar_lista_equipamentos(self):
        self.lista_equipamentos.delete("1.0", "end")  # Limpa o texto atual
        
        try:
            self.cursor.execute('''
            SELECT e.nome, e.descricao, e.quantidade, 
                (SELECT COUNT(*) FROM unidades_equipamento ue 
                    WHERE ue.equipamento_id = e.id AND ue.disponivel = 1) as disponiveis
            FROM equipamentos e
            ORDER BY e.nome
            ''')
            
            equipamentos = self.cursor.fetchall()
            
            if not equipamentos:
                self.lista_equipamentos.insert("end", "Nenhum equipamento cadastrado.\n")
                return
                
            for equip in equipamentos:
                texto = (f"Nome: {equip[0]}\n"
                        f"Descrição: {equip[1]}\n"
                        f"Quantidade total: {equip[2]}\n"
                        f"Unidades disponíveis: {equip[3]}\n"
                        "----------------------------\n")
                self.lista_equipamentos.insert("end", texto)
                
        except Exception as e:
            print(f"Erro ao carregar lista de equipamentos: {e}")
            self.lista_equipamentos.insert("end", "Erro ao carregar equipamentos.\n")
    
    def atualizar_lista_unidades(self):
        self.lista_unidades.delete("1.0", "end")
        self.cursor.execute('''
        SELECT e.nome, ue.codigo, 
               CASE WHEN ue.disponivel = 1 THEN 'Disponível' ELSE 'Emprestado' END as status
        FROM unidades_equipamento ue
        JOIN equipamentos e ON ue.equipamento_id = e.id
        ''')
        for row in self.cursor.fetchall():
            self.lista_unidades.insert("end", 
                f"Equipamento: {row[0]}\nUnidade: {row[1]}\nStatus: {row[2]}\n\n")
    
    def atualizar_lista_usuarios(self):
        self.lista_usuarios.delete("1.0", "end")
        self.cursor.execute('''
        SELECT nome, matricula, email,
               (SELECT COUNT(*) FROM emprestimos WHERE usuario_id = usuarios.id AND data_devolucao_real IS NULL) as emprestimos_ativos
        FROM usuarios
        ''')
        for row in self.cursor.fetchall():
            self.lista_usuarios.insert("end", 
                f"Nome: {row[0]}\nMatrícula: {row[1]}\nEmail: {row[2]}\nEmpréstimos ativos: {row[3]}\n\n")
    
    # Relatórios
    def mostrar_emprestimos_ativos(self):
        self.area_relatorio.delete("1.0", "end")
        self.cursor.execute('''
        SELECT u.nome, e.nome, ue.codigo, emp.data_emprestimo, emp.data_devolucao_prevista
        FROM emprestimos emp
        JOIN usuarios u ON emp.usuario_id = u.id
        JOIN unidades_equipamento ue ON emp.unidade_id = ue.id
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE emp.data_devolucao_real IS NULL
        ORDER BY emp.data_devolucao_prevista
        ''')
        
        self.area_relatorio.insert("end", "EMPRÉSTIMOS ATIVOS:\n\n")
        for row in self.cursor.fetchall():
            self.area_relatorio.insert("end", 
                f"Usuário: {row[0]}\nEquipamento: {row[1]} (Unidade: {row[2]})\n"
                f"Data empréstimo: {row[3]}\nDevolução prevista: {row[4]}\n\n")
    
    def mostrar_historico_completo(self):
        self.area_relatorio.delete("1.0", "end")
        self.cursor.execute('''
        SELECT u.nome, e.nome, ue.codigo, emp.data_emprestimo, emp.data_devolucao_prevista, emp.data_devolucao_real
        FROM emprestimos emp
        JOIN usuarios u ON emp.usuario_id = u.id
        JOIN unidades_equipamento ue ON emp.unidade_id = ue.id
        JOIN equipamentos e ON ue.equipamento_id = e.id
        ORDER BY emp.data_emprestimo DESC
        ''')
        
        self.area_relatorio.insert("end", "HISTÓRICO COMPLETO:\n\n")
        for row in self.cursor.fetchall():
            devolucao = row[5] if row[5] else "Não devolvido"
            self.area_relatorio.insert("end", 
                f"Usuário: {row[0]}\nEquipamento: {row[1]} (Unidade: {row[2]})\n"
                f"Data empréstimo: {row[3]}\nDevolução prevista: {row[4]}\n"
                f"Devolução real: {devolucao}\n\n")
    
    def mostrar_atrasados(self):
        self.area_relatorio.delete("1.0", "end")
        hoje = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
        SELECT u.nome, e.nome, ue.codigo, emp.data_emprestimo, emp.data_devolucao_prevista
        FROM emprestimos emp
        JOIN usuarios u ON emp.usuario_id = u.id
        JOIN unidades_equipamento ue ON emp.unidade_id = ue.id
        JOIN equipamentos e ON ue.equipamento_id = e.id
        WHERE emp.data_devolucao_real IS NULL 
        AND emp.data_devolucao_prevista < ?
        ORDER BY emp.data_devolucao_prevista
        ''', (hoje,))
        
        self.area_relatorio.insert("end", "EQUIPAMENTOS ATRASADOS:\n\n")
        for row in self.cursor.fetchall():
            self.area_relatorio.insert("end", 
                f"Usuário: {row[0]}\nEquipamento: {row[1]} (Unidade: {row[2]})\n"
                f"Data empréstimo: {row[3]}\nDevolução prevista: {row[4]}\n\n")
    
    def mostrar_trocas(self):
        self.area_relatorio.delete("1.0", "end")
        self.cursor.execute('''
        SELECT u.nome, 
               e1.nome as equip_antigo, ue1.codigo as unid_antiga,
               e2.nome as equip_novo, ue2.codigo as unid_nova,
               t.data_troca, t.motivo
        FROM trocas t
        JOIN emprestimos emp ON t.emprestimo_id = emp.id
        JOIN usuarios u ON emp.usuario_id = u.id
        JOIN unidades_equipamento ue1 ON t.unidade_antiga_id = ue1.id
        JOIN equipamentos e1 ON ue1.equipamento_id = e1.id
        JOIN unidades_equipamento ue2 ON t.unidade_nova_id = ue2.id
        JOIN equipamentos e2 ON ue2.equipamento_id = e2.id
        ORDER BY t.data_troca DESC
        ''')
        
        self.area_relatorio.insert("end", "HISTÓRICO DE TROCAS:\n\n")
        for row in self.cursor.fetchall():
            self.area_relatorio.insert("end", 
                f"Usuário: {row[0]}\n"
                f"Equipamento antigo: {row[1]} (Unidade: {row[2]})\n"
                f"Equipamento novo: {row[3]} (Unidade: {row[4]})\n"
                f"Data da troca: {row[5]}\nMotivo: {row[6]}\n\n")
            


    def exportar_relatorio_pdf(self):
        texto = self.area_relatorio.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("Aviso", "Não há conteúdo no relatório para exportar.")
            return

        caminho = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not caminho:
            return

        try:
            c = canvas.Canvas(caminho, pagesize=A4)
            largura, altura = A4
            y = altura - 50
            linhas = texto.split("\n")

            for linha in linhas:
                if y < 50:  # Nova página se chegar no rodapé
                    c.showPage()
                    y = altura - 50
                c.drawString(50, y, linha)
                y -= 15  # Espaçamento entre linhas

            c.save()
            messagebox.showinfo("Sucesso", f"Relatório exportado para PDF com sucesso:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {str(e)}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = SistemaEmprestimo(root)
    root.mainloop()