# Sistema de Inventário de Ativos de TI e Gestão de Vulnerabilidades (Versão SQLite)

Este projeto é uma aplicação de linha de comando (CLI) desenvolvida em Python para o gerenciamento centralizado do ciclo de vida de ativos de infraestrutura de TI e o acompanhamento de suas respectivas vulnerabilidades de segurança. Esta versão utiliza o **SQLite** como motor de banco de dados relacional, garantindo persistência robusta, integridade referencial e consultas otimizadas diretamente em um arquivo local (`inventario_seguranca.db`).

---

## 🛠️ Funcionalidades (Requisitos do Sistema)

O sistema implementa um fluxo completo de **CRUD** (Create, Read, Update, Delete) integrado a regras de governança e conformidade em cibersegurança:

1. **Cadastrar Ativo de TI**: Registra dispositivos com ID único obrigatório, hostname, responsável, setor e categoria (via Enum). O sistema realiza a validação de disponibilidade do ID único logo no início do fluxo para otimizar a experiência do usuário.
2. **Consultar Ativos (Central Unificada)**: Permite buscas flexíveis através de um menu interno:
   * **Por ID Único**: Busca direta por chave primária (`fetchone`).
   * **Por Hostname**: Busca por varredura insensível a maiúsculas/minúsculas (`LOWER()`). Caso existam múltiplos ativos com o mesmo hostname, o sistema exibe uma listagem inteligente para o operador diferenciá-los por ID.
   * **Listar Todos**: Renderiza um painel geral estruturado com todos os ativos do inventário.
3. **Atualizar Cadastro de Ativo**: Permite modificar Hostname, Responsável e Setor de um registro existente. O sistema carrega os dados atuais como padrão e solicita confirmação explícita (`S/N`) antes de consolidar a transação.
4. **Remover Ativos (Em Lote)**: Permite a exclusão de um ou múltiplos ativos simultaneamente, inserindo os IDs separados por vírgula (ex: `1, 2, 5`). Realiza a remoção automática em cascata de todas as vulnerabilidades vinculadas.
5. **Cadastrar Vulnerabilidade por Ativo**: Associa falhas de segurança a um ativo válido, coletando descrição, categoria, nível de severidade e status de tratamento. O ID da vulnerabilidade é gerado de forma incremental e automática pelo banco.
6. **Visualizar Relatório de Vulnerabilidades**: Renderiza na tela um relatório detalhado e formatado com o cabeçalho do ativo e todas as ameaças atreladas a ele.

---

## 🧠 Decisões Arquiteturais e Boas Práticas de Cibersegurança

Para atender aos rigorosos critérios de segurança e desempenho, a aplicação foi estruturada sob os seguintes pilares:

* **Arquitetura Relacional e Normalização**: Os dados foram divididos em duas tabelas distintas (`ativos` e `vulnerabilidades`), eliminando a redundância e aplicando o conceito de Chave Estrangeira (*Foreign Key*).
* **Mitigação de SQL Injection**: Todas as consultas e inserções no banco de dados utilizam **consultas parametrizadas** (argumentos com `?`). Os dados inseridos pelo usuário são tratados como literais pelo driver do SQLite, impedindo ataques de injeção de código malicioso.
* **Integridade em Cascata (`ON DELETE CASCADE`)**: A restrição de chave estrangeira foi configurada para propagar deleções. Ao remover um ativo, o próprio motor do banco limpa os registros dependentes na tabela de vulnerabilidades, evitando dados órfãos (*garbage collection* a nível de banco).
* **Atomicidade de Transações**: Operações de escrita (`INSERT`, `UPDATE`, `DELETE`) utilizam o método `conexao.commit()`. Isso garante que as alterações só sejam gravadas no disco se todo o fluxo for executado com sucesso, prevenindo corrupção do arquivo por falhas operacionais.
* **Formatação Visual Profissional**: A exibição de tabelas utiliza alinhamento e espaçamento de largura fixa no terminal (ex: `{valor:<18}`), garantindo a legibilidade e organização visual de relatórios extensos.

---

## 📁 Modelo Entidade-Relacionamento (Esquema SQL)

O arquivo `inventario_seguranca.db` armazena os dados seguindo a estrutura relacional abaixo:

### Tabela `ativos`
* `id` (INTEGER, PRIMARY KEY) -> Chave primária definida pelo usuário.
* `hostname` (TEXT, NOT NULL) -> Nome de identificação da máquina.
* `responsavel` (TEXT, NOT NULL) -> Operador ou dono do ativo.
* `setor` (TEXT, NOT NULL) -> Setor corporativo responsável.
* `tipo` (INTEGER, NOT NULL) -> Código numérico mapeado pelo `Enum`.

### Tabela `vulnerabilidades`
* `id` (INTEGER, PRIMARY KEY AUTOINCREMENT) -> Código sequencial automático.
* `ativo_id` (INTEGER, NOT NULL) -> Chave Estrangeira ligada à tabela `ativos`.
* `descricao` (TEXT, NOT NULL) -> Detalhes ou código CVE da falha.
* `categoria` (TEXT, NOT NULL) -> Classificação técnica do risco.
* `severidade` (TEXT, NOT NULL) -> Impacto estimado (Baixa, Média, Alta, Crítica).
* `status` (TEXT, NOT NULL) -> Estado de mitigação (Aberta, Em tratamento, Corrigida, Aceita).

*Restrição: `FOREIGN KEY(ativo_id) REFERENCES ativos(id) ON DELETE CASCADE`*

---
