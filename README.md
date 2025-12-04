# Projeto de Chamada de Procedimento Remoto (RPC) com RabbitMQ

Esta atividade consiste em um sistema distribuído utilizando RabbitMQ com RPC, em Python.

## Arquitetura

O sistema é composto por dois componentes principais que se comunicam através de filas no RabbitMQ:

1. Cliente ("rpc_client.py"): Inicia a chamada RPC, enviando a requisição diretamente para a fila do serviço desejado e aguardando a resposta em uma fila de *callback* exclusiva.
2. Serviços ("services/*.py"): Consomem as requisições de suas respectivas filas, processam a lógica de negócio e enviam a resposta de volta para a fila de *callback* do cliente.

## Pré-requisitos

Para executar este projeto, você precisará ter instalado:

*   Python
*   RabbitMQ Server

## Instale as dependências

Instale a biblioteca "pika" para comunicação com o RabbitMQ, no terminal, através do comando:

``` pip install -r requeriments.txt ```

## Estrutura do Projeto

```
sistemas-distribuidos-rpc/
├── client/
│   └── __init__.py
│   └── rpc_client.py
├── common/
│   └── __init__.py
│   └── rpc_utils.py
├── services/
│    └── __init__.py
│    └── service_busca.py
│    └── service_conversao.py
│    └── service_media.py
│    └── service_soma.py
├── .gitignore
└── requeriments.txt
```

## Como Executar

### 1. Iniciar os Serviços

Cada serviço deve ser executado em um terminal separado. Certifique-se de que o RabbitMQ esteja em execução.

Terminal 1: Serviço de Soma

``` python -m services.service_soma ```

Terminal 2: Serviço de Média

``` python -m services.service_media ```

Terminal 3: Serviço de Busca

``` python -m services.service_busca ```

Terminal 4: Serviço de Conversão de Temperatura

``` python -m services.service_conversao ```

### 2. Executar o Cliente

Execute o cliente em um terminal separado. Ele vai solicitar qual serviço você deseja chamar e os parâmetros necessários.

``` python -m client.rpc_client ```

O cliente irá listar os serviços disponíveis: "soma", "media", "busca" e "conversao"

## Exemplo de um serviço

Ao executar o cliente, escolha "conversao":

```
Escolha o serviço: soma, media, busca, conversao
Serviço: conversao
Temperatura em Celsius: 0
Chamando serviço 'conversao' com payload: {'celsius': 0.0}
Resultado: {'resultado em fahrenheit': 32.0}
```

## Fluxo

Cliente -> Fila do Serviço -> Serviço -> Fila de Callback do Cliente -> Cliente
