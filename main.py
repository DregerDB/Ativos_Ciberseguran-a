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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY,
        hostname TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        setor TEXT NOT NULL,
        tipo INTEGER NOT NULL # utilizando o Enum
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

    while True:
        try:
            id_ativo = int(input("Insira o ID do Ativo de TI (apenas números): ").strip())
            if id_ativo <= 0:
                print("❌ Erro: O ID deve ser um número positivo maior que zero.")
                continue

            # Verifica no banco de dados se o ID já existe antes de continuar
            cursor.execute("SELECT id FROM ativos WHERE id = ?;", (id_ativo,))
            if cursor.fetchone() is not None:
                print(f"❌ Erro: Já existe um ativo cadastrado com o ID {id_ativo}! Escolha outro.")
                continue

            break  # ID válido e disponível, sai do loop do ID
        except ValueError:
            print("❌ Erro: Entrada inválida! Digite um número inteiro.")

    hostname = input("Insira o nome do hostname (ex: srv-web-01): ").strip()
    while not hostname:
        print("❌ O campo Hostname não pode estar vazio.")
        hostname = input("Insira o nome do hostname: ").strip()

    responsavel = input("Digite o nome do responsável pelo ativo: ").strip()
    while not responsavel or not responsavel.replace(" ", "").isalpha():
        print("❌ O campo Responsável deve conter apenas letras e não pode estar vazio.")
        responsavel = input("Digite o nome do responsável: ").strip()

    setor = input("Digite o nome do setor (ex: TI, Financeiro): ").strip().capitalize()
    while not setor or not setor.replace(" ", "").isalpha():
        print("❌ O campo Setor deve conter apenas letras e não pode estar vazio.")
        setor = input("Digite o nome do setor: ").strip()

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
        print(f"\n✅ Ativo '{hostname}' (ID: {id_ativo}) cadastrado com sucesso no Banco!")

    except sqlite3.IntegrityError:
        print(f"\n❌ Erro de Integridade: O ID {id_ativo} foi ocupado por outra sessão.")

    finally:
        conexao.close()


def buscar_ativo():
    """Permite buscar por ID, Hostname ou Listar todos (SQLITE)."""
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
    """Função para desenhar o bloco de dados de um único ativo encontrado."""
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

    try:
        id_atualizar = int(input("Insira o ID do ativo que deseja atualizar: ").strip())
    except ValueError:
        print("❌ Erro: O ID deve ser un número inteiro positivo.")
        conexao.close()
        return

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

    novo_hostname = input(f"Hostname antigo: [{hostname_atual}] Insira o novo hostname: ").strip()
    if not novo_hostname:
        novo_hostname = hostname_atual

    while True:
        novo_resp = input(f"Responsável antigo: [{resp_atual}] Novo Responsável: ").strip()
        if not novo_resp:
            novo_resp = resp_atual
            break
        if novo_resp.replace(" ", "").isalpha():
            break
        print("❌ Erro: O nome do Responsável deve conter apenas letras.")

    while True:
        novo_setor = input(f"Setor antigo: [{setor_atual}] Novo Setor: ").strip()
        if not novo_setor:
            novo_setor = setor_atual
            break
        if novo_setor.replace(" ", "").isalpha():
            break
        print("❌ Erro: O nome do Setor deve conter apenas letras.")

    print("\n" + "-" * 40)
    print("⚠️  RESUMO DAS ALTERAÇÕES:")
    print(f"  Hostname:    {hostname_atual} -> {novo_hostname}")
    print(f"  Responsável: {resp_atual} -> {novo_resp}")
    print(f"  Setor:       {setor_atual} -> {novo_setor}")
    print("-" * 40)

    confirmacao = input("Deseja confirmar estas alterações? (S/N): ").strip().upper()

    if confirmacao == 'S':
        try:
            # Executa o comando UPDATE com marcadores (Proteção contra SQL Injection)
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

def cadastrar_vulnerabilidade():
    """Associa uma nova vulnerabilidade ao histórico de um ativo existente no SQLite."""
    print("\n--- CADASTRO DE VULNERABILIDADE (SQLITE) ---")
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # 1. Verificar se o ativo alvo existe no banco de dados
    try:
        id_ativo = int(input("Digite o ID do ativo que possui a vulnerabilidade: ").strip())
    except ValueError:
        print("❌ Erro: O ID do ativo deve ser um número inteiro positivo.")
        conexao.close()
        return

    # Consulta para checar a existência do ativo e pegar o hostname/tipo
    cursor.execute("SELECT hostname, tipo FROM ativos WHERE id = ?;", (id_ativo,))
    ativo = cursor.fetchone()

    if not ativo:
        print(f"❌ Erro: Nenhum ativo encontrado com o ID {id_ativo}. Não é possível cadastrar a falha.")
        conexao.close()
        return

    hostname, codigo_tipo = ativo
    try:
        nome_tipo = TipoAtivo(codigo_tipo).name.capitalize()
    except ValueError:
        nome_tipo = "Desconhecido"

    print(f"\n✅ Ativo localizado: {hostname} ({nome_tipo})")
    print("Insira os dados da falha de segurança abaixo:")

    # 2. Captura e Validação da Descrição
    descricao = input("Descrição da falha (ex: CVE-2023-38606 ou Brecha no SSH): ").strip()
    while not descricao:
        print("❌ A descrição não pode estar vazia.")
        descricao = input("Descrição da falha: ").strip()

    # 3. Captura e Validação da Categoria
    categoria = input("Categoria da vulnerabilidade (ex: Injeção de Código, Patch Ausente): ").strip()
    while not categoria:
        print("❌ A categoria não pode estar vazia.")
        categoria = input("Categoria da vulnerabilidade: ").strip()

    # 4. Seleção de Severidade (Tupla de validação)
    severidades_validas = ("Baixa", "Média", "Alta", "Crítica")
    print("\nNíveis de Severidade:")
    for i, sev in enumerate(severidades_validas, 1):
        print(f"  [{i}] - {sev}")

    while True:
        try:
            opcao_sev = int(input("Escolha o número da severidade (1-4): ").strip())
            if 1 <= opcao_sev <= len(severidades_validas):
                severidade = severidades_validas[opcao_sev - 1]
                break
            print("❌ Opção inválida! Escolha um número de 1 a 4.")
        except ValueError:
            print("❌ Erro: Insira um número inteiro positivo.")

    # 5. Seleção de Status Inicial
    status_validos = ("Aberta", "Em tratamento", "Corrigida", "Aceita")
    print("\nStatus Inicial da Vulnerabilidade:")
    for i, st in enumerate(status_validos, 1):
        print(f"  [{i}] - {st}")

    while True:
        try:
            opcao_st = int(input("Escolha o número do status (1-4): ").strip())
            if 1 <= opcao_st <= len(status_validos):
                status = status_validos[opcao_st - 1]
                break
            print("❌ Opção inválida! Escolha um número de 1 a 4.")
        except ValueError:
            print("❌ Erro: Insira um número inteiro positivo.")

    # 6. Inserção Parametrizada na tabela 'vulnerabilidades'
    try:
        cursor.execute("""
                       INSERT INTO vulnerabilidades (ativo_id, descricao, categoria, severidade, status)
                       VALUES (?, ?, ?, ?, ?);
                       """, (id_ativo, descricao, categoria, severidade, status))

        conexao.commit()
        print(f"\n✅ Vulnerabilidade registrada com sucesso e vinculada ao ativo '{hostname}'!")
    except sqlite3.Error as erro:
        print(f"❌ Erro ao salvar a vulnerabilidade no banco: {erro}")
    finally:
        conexao.close()


def visualizar_vulnerabilidades():
    """Exibe um relatório detalhado de todas as vulnerabilidades de um ativo específico (SQLITE)."""
    print("\n--- RELATÓRIO DE VULNERABILIDADES POR ATIVO ---")
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # 1. Localizar o ativo pelo ID para extrair o cabeçalho do relatório
    try:
        id_ativo = int(input("Digite o ID do ativo que deseja consultar: ").strip())
    except ValueError:
        print("❌ Erro: O ID deve ser um número inteiro positivo.")
        conexao.close()
        return

    # Consulta rápida para verificar se o ativo existe e coletar seus dados
    cursor.execute("SELECT hostname, setor, responsavel FROM ativos WHERE id = ?;", (id_ativo,))
    ativo = cursor.fetchone()

    if not ativo:
        print(f"❌ Nenhum ativo encontrado com o ID {id_ativo}.")
        conexao.close()
        return

    hostname, setor, responsavel = ativo

    # Desenha o cabeçalho elegante do relatório
    print("\n" + "=" * 50)
    print(f" ATIVO: {hostname} | Setor: {setor}")
    print(f" Responsável: {responsavel}")
    print("=" * 50)

    # 2. Buscar as vulnerabilidades vinculadas a este ativo_id
    cursor.execute("""
                   SELECT descricao, categoria, severidade, status
                   FROM vulnerabilidades
                   WHERE ativo_id = ?;
                   """, (id_ativo,))
    lista_vulns = cursor.fetchall()

    # 3. Verificar se o ativo possui registros de falhas
    if not lista_vulns:
        print("✅ Excelente! Nenhuma vulnerabilidade registrada para este ativo.")
        print("=" * 50)
        conexao.close()
        return

    print(f"⚠️  Foram encontradas {len(lista_vulns)} vulnerabilidade(s):")
    print("-" * 50)

    # 4. Percorrer e listar cada vulnerabilidade de forma estruturada
    for i, vuln in enumerate(lista_vulns, 1):
        descricao, categoria, severidade, status = vuln
        print(f" [{i}] Descrição:  {descricao}")
        print(f"     Categoria:  {categoria}")
        print(f"     Severidade: {severidade}")
        print(f"     Status:     {status}")
        print("-" * 50)

    conexao.close()


def main():
    while True:
        print("\n=== SISTEMA DE SEGURANÇA SQLITE ===")
        print("1. Cadastrar Ativo")
        print("2. Buscar Ativo")
        print("3. Atualizar Ativo")
        print("4. Remover Ativo")
        print("5. Cadastrar Vulnerabilidade")
        print("6. Visualizar Vulnerabilidade")
        print("0. Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_ativo()
        elif opcao == "2":
            buscar_ativo()
        elif opcao == "3":
            atualizar_ativo()
        elif opcao == "4":
            remover_ativo()
        elif opcao == "5":
            cadastrar_vulnerabilidade()
        elif opcao == "6":
            visualizar_vulnerabilidades()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida!")


if __name__ == "__main__":
    main()
