import sqlite3
from enum import Enum

# Nome do arquivo do banco de dados
DB_NAME = "inventario_seguranca.db"

class TipoAtivo(Enum):
    NOTEBOOK = 1
    SERVIDOR = 2
    ROTEADOR = 3
    APLICACAO_WEB = 4

def conectar_banco():
    """Estabelece conexão com p arquivo SQLite e ativa suporte a chaves estrangeiras."""
    conexao = sqlite3.connect(DB_NAME)
    # Garante que o SQLite force a remoção em cascata (Foreign Keys)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    """Cria as tabelas necessárias para o banco de dados.( caso não existam)."""
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Criação da tabela de Ativos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY,
        hostname TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        setor TEXT NOT NULL,
        tipo INTEGER NOT NULL
    );
    """)

# Criação da tabela de Vulnerabilidades (com relacionamento Cascata)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vulnerabilidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ativo_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        severidade TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE
    );
    """)
    conexao.commit()
    conexao.close()
# Inicializa o banco de dados assim que o script roda
inicializar_banco()
print("🎯 Banco de Dados SQLite inicializado e pronto para uso!")


def cadastrar_ativo():
    """Cadastra um novo ativo verificando a duplicidade do ID logo no início (SQLITE)."""
    print("\n--- CADASTRO DE NOVO ATIVO (SQLITE) ---")
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # 1. Validação, Captura e Verificação Imediata do ID
    while True:
        try:
            id_ativo = int(input("Insira o ID do Ativo de TI (apenas números): ").strip())
            if id_ativo <= 0:
                print("❌ Erro: O ID deve ser um número positivo maior que zero.")
                continue

            # NOVO: Verifica no banco de dados se o ID já existe antes de continuar
            cursor.execute("SELECT id FROM ativos WHERE id = ?;", (id_ativo,))
            if cursor.fetchone() is not None:
                print(f"❌ Erro: Já existe um ativo cadastrado com o ID {id_ativo}! Escolha outro.")
                continue  # Volta para o início do loop pedindo um novo ID

            break  # ID válido e disponível, sai do loop do ID
        except ValueError:
            print("❌ Erro: Entrada inválida! Digite um número inteiro.")

    # 2. Captura e Validação do Hostname (O usuário só chega aqui se o ID estiver livre!)
    hostname = input("Insira o nome do hostname (ex: srv-web-01): ").strip()
    while not hostname:
        print("❌ O campo Hostname não pode estar vazio.")
        hostname = input("Insira o nome do hostname: ").strip()

    # 3. Captura e Validação do Responsável
    responsavel = input("Digite o nome do responsável pelo ativo: ").strip()
    while not responsavel or not responsavel.replace(" ", "").isalpha():
        print("❌ O campo Responsável deve conter apenas letras e não pode estar vazio.")
        responsavel = input("Digite o nome do responsável: ").strip()

    # 4. Captura e Validação do Setor
    setor = input("Digite o nome do setor (ex: TI, Financeiro): ").strip().capitalize()
    while not setor or not setor.replace(" ", "").isalpha():
        print("❌ O campo Setor deve conter apenas letras e não pode estar vazio.")
        setor = input("Digite o nome do setor: ").strip()

    # 5. Exibição das Categorias vindas do Enum
    print("\nCategorias de Ativos disponíveis:")
    for tipo in TipoAtivo:
        print(f"   [{tipo.value}] - {tipo.name}")

    while True:
        try:
            escolha_tipo = int(input("Escolha o número da categoria: ").strip())
            if escolha_tipo in [t.value for t in TipoAtivo]:
                break

            print("❌ Opção inválida! Escolha um dos números listados acima.")
        except ValueError:
            print("❌ Erro: Digite apenas o número inteiro da categoria.")

    # 6. Inserção Segura no Banco de Dados (O IntegrityError aqui vira apenas uma proteção extra)
    try:
        cursor.execute("""
                       INSERT INTO ativos (id, hostname, responsavel, setor, tipo)
                       VALUES (?, ?, ?, ?, ?);
                       """, (id_ativo, hostname, responsavel, setor, escolha_tipo))

        conexao.commit()
        print(f"\n✅ Ativo '{hostname}' (ID: {id_ativo}) cadastrado e persistido com sucesso no SQLite!")

    except sqlite3.IntegrityError:
        print(f"\n❌ Erro de Integridade: O ID {id_ativo} foi ocupado por outra sessão.")

    finally:
        conexao.close()
