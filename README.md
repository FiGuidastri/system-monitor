# Monitor de Uso de Programas no Windows

Este projeto registra o tempo de uso de programas em computadores com Windows, salvando os dados em um banco de dados MySQL para posterior análise. Ele também coleta a lista de programas instalados na máquina.

## 🚀 Funcionalidades

- ⏱️ Monitoramento automático do tempo de execução de programas
- 🗃️ Registro da lista de programas instalados por usuário
- 🧠 Banco de dados MySQL com estrutura otimizada para consultas

### 🛠️ Requisitos
Python 3.8+

MySQL (local ou remoto)

### Sistema operacional: Windows

📊 Tabelas no Banco de Dados

- program_usage_summary

    Coluna|Tipo|Descrição
    |---|---|---|
    id|INT|Chave primária
    user|VARCHAR|Nome do usuário do Windows
    machine_name|	VARCHAR	|Nome do computador
    program_name|	VARCHAR|	Nome do processo
    total_seconds|	DOUBLE|	Tempo total de execução acumulado
    last_updated|	TIMESTAMP|	Última atualização do registro
    |---|---|---|


- installed_programs

    Coluna|Tipo|Descrição
    |---|---|---|
    id	|INT	|Chave primária
    user	|VARCHAR|	Nome do usuário do Windows
    program_name	|VARCHAR|	Nome do programa
    version|	VARCHAR|	Versão do programa
    publisher|	VARCHAR|	Publicador (Microsoft, etc)
    install_location	|TEXT|	Caminho de instalação
    last_checked|	TIMESTAMP|	Data da última verificação

### 📌 Observações
O script deve ser executado com permissões adequadas para acessar o registro do Windows.

O monitoramento roda indefinidamente até ser interrompido.

### 📄 Licença
Este projeto é de uso pessoal ou empresarial interno. Para uso comercial/distribuição, consulte a licença ou o autor.

