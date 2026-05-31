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


def buscar_ativo():
    """Central de Consultas: Permite buscar por ID, Hostname ou Listar todos (SQLITE)."""
    print("\n--- CONSULTA DE ATIVOS ---")

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        print("Como deseja realizar a consulta?")
        print("1. Buscar por ID Único")
        print("2. Buscar por Hostname")
        print("3. Listar TODOS os ativos cadastrados")
        opcao_busca = int(input("Escolha uma opção (1-3): ").strip())
    except ValueError:
        print("❌ Erro: Digite um número inteiro válido (1, 2 ou 3).")
        conexao.close()
        return

    if opcao_busca == 1:
        try:
            id_busca = int(input("Insira o ID do ativo de busca: ").strip())
        except ValueError:
            print("❌ Erro: O ID deve ser um número inteiro.")
            conexao.close()
            return

        # Consulta filtrando pelo ID único
        cursor.execute("SELECT id, hostname, responsavel, setor, tipo FROM ativos WHERE id = ?;", (id_busca,))
        ativo = cursor.fetchone()  # fetchone() traz apenas uma linha (ou None se não achar)

        if ativo:
            exibir_card_individual(ativo)
        else:
            print(f"❌ Nenhum ativo encontrado com o ID {id_busca}.")


    elif opcao_busca == 2:
        hostname_busca = input("Insira o nome do hostname: ").strip().lower()
        if not hostname_busca:
            print("❌ O campo hostname de busca não pode estar vazio.")
            conexao.close()
            return
        # Buscamos TODOS os ativos com esse nome usando fetchall()
        cursor.execute("SELECT id, hostname, responsavel, setor, tipo FROM ativos WHERE LOWER(hostname) = ?;",
                       (hostname_busca,))
        ativos_encontrados = cursor.fetchall()
        if not ativos_encontrados:
            print(f"❌ Nenhum ativo encontrado com o hostname '{hostname_busca}'.")
        elif len(ativos_encontrados) == 1:
            # Se achou apenas um, exibe o card completo direto
            exibir_card_individual(ativos_encontrados[0])
        else:
            # Se houver hostnames idênticos, exibe uma lista para o usuário diferenciar pelo ID
            print(f"\n⚠️  Aviso: Foram encontrados {len(ativos_encontrados)} ativos com o mesmo hostname!")
            print("Use a busca por ID Único para ver os detalhes de um ativo específico.")
            print("\n" + "=" * 70)
            print(f"{'ID':<6} | {'HOSTNAME':<18} | {'RESPONSÁVEL':<20} | {'SETOR':<15}")
            print("=" * 70)
            for linha in ativos_encontrados:
                id_ativo, hostname, responsavel, setor, _ = linha
                print(f"{id_ativo:<6} | {hostname:<18} | {responsavel:<20} | {setor:<15}")
            print("=" * 70)

    elif opcao_busca == 3:
        cursor.execute("SELECT id, hostname, responsavel, setor, tipo FROM ativos ORDER BY id;")
        ativos = cursor.fetchall()

        if not ativos:
            print("🛈 O inventário está vazio. Não há ativos cadastrados.")
            conexao.close()
            return

        print("\n" + "=" * 85)
        print(f"{'ID':<6} | {'HOSTNAME':<18} | {'RESPONSÁVEL':<20} | {'SETOR':<15} | {'CATEGORIA':<12}")
        print("=" * 85)

        for linha in ativos:
            id_ativo, hostname, responsavel, setor, codigo_tipo = linha
            try:
                nome_tipo = TipoAtivo(codigo_tipo).name.capitalize()
            except ValueError:
                nome_tipo = "Desconhecido"
            print(f"{id_ativo:<6} | {hostname:<18} | {responsavel:<20} | {setor:<15} | {nome_tipo:<12}")
        print("=" * 85)

    else:
        print("❌ Opção de busca inválida.")

    conexao.close()


def exibir_card_individual(linha_ativo):
    """Função auxiliar para desenhar o bloco de dados de um único ativo encontrado."""
    id_real, hostname, responsavel, setor, codigo_tipo = linha_ativo

    try:
        nome_tipo = TipoAtivo(codigo_tipo).name.capitalize()
    except ValueError:
        nome_tipo = "Desconhecido"

    print("\n" + "=" * 35)
    print("\t DADOS DO ATIVO ENCONTRADO \t")
    print("=" * 35)
    print(f"ID:           {id_real}")
    print(f"Hostname:     {hostname}")
    print(f"Responsável:  {responsavel}")
    print(f"Setor:        {setor}")
    print(f"Tipo/Categoria: {nome_tipo} (código: {codigo_tipo})")
    print("=" * 35)

def atualizar_ativo():
    """Permite alterar o hostname, responsável e setor de um ativo no SQLite com confirmação."""
    print("\n--- ATUALIZAÇÃO DE ATIVO (SQLITE) ---")
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # 1. Localizar o ativo pelo ID
    try:
        id_atualizar = int(input("Insira o ID do ativo que deseja atualizar: ").strip())
    except ValueError:
        print("❌ Erro: O ID deve ser un número inteiro positivo.")
        conexao.close()
        return

    # Procura os dados atuais do ativo no banco
    cursor.execute("SELECT hostname, responsavel, setor, tipo FROM ativos WHERE id = ?;", (id_atualizar,))
    ativo = cursor.fetchone()

    if not ativo:
        print(f"❌ Nenhum ativo encontrado com o ID {id_atualizar}.")
        conexao.close()
        return

    # Desempacota os dados atuais carregados do banco
    hostname_atual, resp_atual, setor_atual, tipo_atual = ativo

    print(f"\nAtivo localizado! A alterar os dados de: {hostname_atual}")
    print("*(Deixe o campo em branco e clique Enter para MANTER o dado atual)*")

    # 2. Captura o Hostname temporariamente
    novo_hostname = input(f"Hostname antigo: [{hostname_atual}] Insira o novo hostname: ").strip()
    if not novo_hostname:
        novo_hostname = hostname_atual

    # 3. Captura o Responsável temporariamente
    while True:
        novo_resp = input(f"Responsável antigo: [{resp_atual}] Novo Responsável: ").strip()
        if not novo_resp:
            novo_resp = resp_atual
            break
        if novo_resp.replace(" ", "").isalpha():
            break
        print("❌ Erro: O nome do Responsável deve conter apenas letras.")

    # 4. Captura o Setor temporariamente
    while True:
        novo_setor = input(f"Setor antigo: [{setor_atual}] Novo Setor: ").strip()
        if not novo_setor:
            novo_setor = setor_atual
            break
        if novo_setor.replace(" ", "").isalpha():
            break
        print("❌ Erro: O nome do Setor deve conter apenas letras.")

    # 5. Exibição do Resumo das Alterações (Antes -> Depois)
    print("\n" + "-" * 40)
    print("⚠️  RESUMO DAS ALTERAÇÕES:")
    print(f"  Hostname:    {hostname_atual} -> {novo_hostname}")
    print(f"  Responsável: {resp_atual} -> {novo_resp}")
    print(f"  Setor:       {setor_atual} -> {novo_setor}")
    print("-" * 40)

    # 6. Solicita a confirmação do utilizador
    confirmacao = input("Deseja confirmar estas alterações? (S/N): ").strip().upper()

    if confirmacao == 'S':
        try:
            # Executa o comando UPDATE de forma parametrizada (Proteção contra SQL Injection)
            cursor.execute("""
                           UPDATE ativos
                           SET hostname    = ?,
                               responsavel = ?,
                               setor       = ?
                           WHERE id = ?;
                           """, (novo_hostname, novo_resp, novo_setor, id_atualizar))

            conexao.commit()
            print(f"\n✅ Dados do ativo ID {id_atualizar} atualizados com sucesso no SQLite!")
        except sqlite3.Error as erro:
            print(f"❌ Erro ao atualizar os dados no banco: {erro}")
    else:
        print("\n❌ Atualização cancelada. Os dados originais foram mantidos intactos.")

    conexao.close()


def remover_ativo():
    """Permite remover um ou múltiplos ativos do inventário de uma só vez (SQLITE)."""
    print("\n--- REMOÇÃO DE ATIVOS (EM LOTE) ---")
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # 1. Captura da entrada do usuário (Ex: "1, 2, 3")
    entrada = input("Digite os IDs dos ativos que deseja remover (separe por vírgula): ").strip()
    if not entrada:
        print("❌ Erro: Nenhum ID foi digitado.")
        conexao.close()
        return

    # Processa a string: separa por vírgula, limpa espaços e converte apenas os números válidos
    lista_ids = []
    for parte in entrada.split(","):
        try:
            num = int(parte.strip())
            if num > 0:
                lista_ids.append(num)
        except ValueError:
            # Ignora caso o usuário digite algo inválido entre as vírgulas (Ex: "1, abc, 3")
            continue

    if not lista_ids:
        print("❌ Erro: Nenhum ID inteiro positivo válido foi identificado.")
        conexao.close()
        return

    # 2. Localizar quais desses ativos realmente existem no banco para mostrar o resumo
    # Criamos marcadores "?" dinâmicos de acordo com o tamanho da lista (Ex: "?, ?, ?")
    marcadores = ",".join(["?"] * len(lista_ids))

    cursor.execute(f"SELECT id, hostname, setor FROM ativos WHERE id IN ({marcadores});", lista_ids)
    ativos_encontrados = cursor.fetchall()

    if not ativos_encontrados:
        print("❌ Nenhum ativo correspondente aos IDs digitados foi encontrado no banco.")
        conexao.close()
        return

    # Atualiza a nossa lista de IDs para conter apenas os que REALMENTE existem (evita alarmes falsos)
    ids_existentes = [ativo[0] for ativo in ativos_encontrados]
    marcadores_reais = ",".join(["?"] * len(ids_existentes))

    # Conta o total de vulnerabilidades que serão apagadas em cascata para todos esses ativos juntos
    cursor.execute(f"SELECT COUNT(*) FROM vulnerabilidades WHERE ativo_id IN ({marcadores_reais});", ids_existentes)
    total_vulns = cursor.fetchone()[0]

    # 3. Tela de aviso crítico listando o que será apagado
    print("\n" + "!" * 50)
    print("⚠️  ATENÇÃO: ESTA AÇÃO NÃO PODE SER DESFEITA!!!!!")
    print(f" Ativos que serão REMOVIDOS do inventário:")
    for ativo in ativos_encontrados:
        print(f"   • ID: {ativo[0]} | Hostname: {ativo[1]:<15} | Setor: {ativo[2]}")
    print(f"\n Total de vulnerabilidades associadas que serão APAGADAS: {total_vulns}")
    print("!" * 50)

    # 4. Confirmação explícita
    confirmacao = input(
        f"\nTem certeza que deseja remover esses {len(ids_existentes)} ativo(s)? [S/N]: ").strip().upper()

    if confirmacao == "S":
        try:
            # Executa o DELETE em lote usando o operador IN
            cursor.execute(f"DELETE FROM ativos WHERE id IN ({marcadores_reais});", ids_existentes)
            conexao.commit()
            print(
                f"\n✅ Sucesso: {len(ids_existentes)} ativo(s) e suas {total_vulns} vulnerabilidades foram limpos do banco!")
        except sqlite3.Error as erro:
            print(f"❌ Erro ao remover os ativos do banco: {erro}")
    else:
        print("\n❌ Remoção em lote cancelada. O inventário permaneceu intacto.")

    conexao.close()

