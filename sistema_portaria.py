import sqlite3
import datetime

class SistemaPortaria:
    def __init__(self):
        """Inicializa o sistema e cria a conexão com o banco de dados."""
        self.conn = sqlite3.connect("portaria.db")
        self.cursor = self.conn.cursor()
        self.criar_tabela()

    def criar_tabela(self):
        """Cria a tabela unificada para todos os cadastros."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cadastros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE NOT NULL,
                bloco TEXT NOT NULL,
                apartamento TEXT NOT NULL,
                placa TEXT,
                tipo TEXT NOT NULL, -- "morador", "visitante", "funcionário", "entregador", "prestador de serviço"
                horario TEXT, -- Para registrar o horário de cadastro
                horario_saida TEXT, -- Para registrar o horário de saída
                tempo_permanencia TEXT -- Para registrar o tempo de permanência
            )
        """)
        self.conn.commit()

    def validar_cpf(self, cpf):
        """Valida um CPF seguindo o algoritmo de dígitos verificadores."""
        cpf = cpf.replace(".", "").replace("-", "")
        if len(cpf) != 11 or not cpf.isdigit() or len(set(cpf)) == 1:
            return False

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        primeiro_dv = (soma * 10 % 11) % 10
        if primeiro_dv != int(cpf[9]):
            return False

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        segundo_dv = (soma * 10 % 11) % 10
        if segundo_dv != int(cpf[10]):
            return False

        return True

    def cadastrar(self, nome, bloco, apartamento, tipo):
        """Cadastra uma pessoa no banco de dados, registrando o horário de cadastro."""
        while True:
            cpf = input("Digite o CPF: ")
            if not self.validar_cpf(cpf):
                print("CPF inválido! Certifique-se de que ele contenha exatamente 11 números e seja válido.")
            else:
                break

        # Verificar se o CPF já existe no banco
        self.cursor.execute("SELECT * FROM cadastros WHERE cpf = ?", (cpf,))
        if self.cursor.fetchone():
            print("Já existe uma pessoa cadastrada com este CPF!")
            return

        placa = None
        resposta = input(f"{nome} possui um carro? (sim/não): ").strip().lower()
        if resposta == "sim":
            placa = input("Digite a placa do carro (ex.: ABC-1234): ").strip().upper()

        # Registrar o horário de cadastro
        horario = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Horário de cadastro registrado para {tipo} {nome}: {horario}")

        self.cursor.execute("""
            INSERT INTO cadastros (nome, cpf, bloco, apartamento, placa, tipo, horario)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, cpf, bloco, apartamento, placa, tipo, horario))
        self.conn.commit()
        print(f"{tipo.capitalize()} cadastrado(a): {nome}, CPF {cpf}, Bloco {bloco}, Apto {apartamento}, Placa: {placa if placa else 'Nenhum carro'}, Horário: {horario}")

    def registrar_saida(self, cpf):
        """Registra a saída de um visitante pelo CPF e calcula o tempo de permanência."""
        self.cursor.execute("SELECT horario FROM cadastros WHERE cpf = ? AND tipo = 'visitante'", (cpf,))
        visitante = self.cursor.fetchone()

        if visitante and visitante[0]: # Verifica se há registro de horário de entrada
            horario_entrada = datetime.datetime.strptime(visitante[0], "%Y-%m-%d %H:%M:%S")
            horario_saida = datetime.datetime.now()
            tempo_permanencia = horario_saida - horario_entrada

            self.cursor.execute("""
                UPDATE cadastros
                SET horario_saida = ?, tempo_permanencia = ?
                WHERE cpf = ? AND tipo = 'visitante'
            """, (horario_saida.strftime("%Y-%m-%d %H:%M:%S"), str(tempo_permanencia), cpf))
            self.conn.commit()

            print(f"Saída registrada para o visitante de CPF {cpf} às {horario_saida}.")
            print(f"Tempo de permanência: {tempo_permanencia}.")
        else:
            print("CPF não encontrado ou o visitante não possui registro de entrada.")

    def listar_cadastros(self, tipo=None):
        """Lista todos os cadastros ou filtra por tipo."""
        if tipo:
            self.cursor.execute("SELECT nome, bloco, apartamento, cpf, placa, horario FROM cadastros WHERE tipo = ?", (tipo,))
        else:
            self.cursor.execute("SELECT nome, bloco, apartamento, cpf, placa, horario, tipo FROM cadastros")

        cadastros = self.cursor.fetchall()

        if cadastros:
            print(f"\n--- {tipo.capitalize() if tipo else 'Todos os Cadastros'} ---")
            for cadastro in cadastros:
                if tipo:
                    nome, bloco, apartamento, cpf, placa, horario = cadastro
                    print(f"{nome} -> Bloco {bloco}, Apto {apartamento}, CPF {cpf}, Placa: {placa if placa else 'Nenhum carro'}, Horário: {horario if horario else 'N/A'}")
                else:
                    nome, bloco, apartamento, cpf, placa, horario, tipo = cadastro
                    print(f"{nome} -> Bloco {bloco}, Apto {apartamento}, CPF {cpf}, Placa: {placa if placa else 'Nenhum carro'}, Tipo: {tipo}, Horário: {horario if horario else 'N/A'}")
        else:
            print(f"Nenhum cadastro encontrado para {tipo if tipo else 'todos'}.")

    def fechar_conexao(self):
        """Fecha a conexão com o banco de dados."""
        self.conn.close()

def menu_cadastro(sistema):
    """Menu de cadastro."""
    while True:
        print("\n--- Menu de Cadastro ---")
        print("1. Cadastrar morador")
        print("2. Cadastrar visitante")
        print("3. Cadastrar funcionário")
        print("4. Cadastrar entregador")
        print("5. Cadastrar prestador de serviço")
        print("6. Retornar ao menu principal")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            nome = input("Digite o nome do morador: ")
            bloco = input("Digite o bloco do morador: ")
            apartamento = input("Digite o apartamento do morador: ")
            sistema.cadastrar(nome, bloco, apartamento, "morador")
        elif escolha == "2":
            nome = input("Digite o nome do visitante: ")
            bloco = input("Digite o bloco visitado: ")
            apartamento = input("Digite o apartamento visitado: ")
            sistema.cadastrar(nome, bloco, apartamento, "visitante")
        elif escolha == "3":
            nome = input("Digite o nome do funcionário: ")
            bloco = input("Digite o bloco onde ele trabalha: ")
            apartamento = "N/A"
            sistema.cadastrar(nome, bloco, apartamento, "funcionário")
        elif escolha == "4":
            nome = input("Digite o nome do entregador: ")
            bloco = input("Digite o bloco da entrega: ")
            apartamento = input("Digite o apartamento da entrega: ")
            sistema.cadastrar(nome, bloco, apartamento, "entregador")
        elif escolha == "5":
            nome = input("Digite o nome do prestador de serviço: ")
            bloco = input("Digite o bloco atendido: ")
            apartamento = input("Digite o apartamento atendido: ")
            sistema.cadastrar(nome, bloco, apartamento, "prestador de serviço")
        elif escolha == "6":
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida. Tente novamente.")

def menu_relatorio(sistema):
    """Menu de relatórios."""
    while True:
        print("\n--- Menu de Relatórios ---")
        print("1. Listar moradores")
        print("2. Listar visitantes")
        print("3. Listar funcionários")
        print("4. Listar entregadores")
        print("5. Listar prestadores de serviço")
        print("6. Retornar ao menu principal")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            sistema.listar_cadastros(tipo="morador")
        elif escolha == "2":
            sistema.listar_cadastros(tipo="visitante")
        elif escolha == "3":
            sistema.listar_cadastros(tipo="funcionário")
        elif escolha == "4":
            sistema.listar_cadastros(tipo="entregador")
        elif escolha == "5":
            sistema.listar_cadastros(tipo="prestador de serviço")
        elif escolha == "6":
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida. Tente novamente.")

def main():
    sistema = SistemaPortaria()
    while True:
        print("\n--- Sistema Portaria ---")
        print("1. Menu de Cadastro")
        print("2. Menu de Relatórios")
        print("3. Registrar saída de visitante")
        print("4. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            menu_cadastro(sistema)
        elif escolha == "2":
            menu_relatorio(sistema)
        elif escolha == "3":
            cpf = input("Digite o CPF do visitante: ")
            sistema.registrar_saida(cpf)
        elif escolha == "4":
            print("Saindo do sistema. Até mais!")
            sistema.fechar_conexao()
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()