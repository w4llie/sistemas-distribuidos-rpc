# coordinator/coordinator.py
import json
import threading
import pika
from common.rpc_utils import get_connection

COORDINATOR_QUEUE = 'rpc_coordinator'
COORDINATOR_RESP_QUEUE = 'coordinator_responses'


class Coordinator:
    def __init__(self):
        # Duas conexões separadas para pedidos e respostas
        self.conn_req = get_connection()
        self.conn_resp = get_connection()

        self.ch_req = self.conn_req.channel()
        self.ch_resp = self.conn_resp.channel()

        # declara filas
        self.ch_req.queue_declare(queue=COORDINATOR_QUEUE)
        self.ch_resp.queue_declare(queue=COORDINATOR_RESP_QUEUE)

        # mapa correlation_id -> reply_to do cliente
        self.pending = {}

        # consumidor das respostas dos serviços
        self.ch_resp.basic_consume(
            queue=COORDINATOR_RESP_QUEUE,
            on_message_callback=self.on_service_response,
            auto_ack=True
        )

    def on_request(self, ch, method, props, body):
        """Recebe pedidos do cliente e encaminha para o serviço correto"""
        try:
            message = json.loads(body)
            service = message.get("service")
            payload = message.get("payload")
        except Exception as e:
            print("Request com formato inválido:", e)
            return

        client_reply_to = props.reply_to
        client_corr_id = props.correlation_id

        if client_reply_to is None or client_corr_id is None:
            print("Cliente não forneceu reply_to ou correlation_id — ignorando")
            return

        # salva para quando o serviço responder
        self.pending[client_corr_id] = client_reply_to
        print(f"[Coordinator] Pedido {client_corr_id} para serviço '{service}', guardado para reply_to={client_reply_to}")

        service_message = {
            "payload": payload,
            "client_corr_id": client_corr_id
        }

        service_queue = f"service_{service}"

        # publica para o serviço
        self.ch_req.basic_publish(
            exchange='',
            routing_key=service_queue,
            properties=pika.BasicProperties(
                reply_to=COORDINATOR_RESP_QUEUE,
                correlation_id=client_corr_id,
                content_type='application/json'
            ),
            body=json.dumps(service_message)
        )

    def on_service_response(self, ch, method, props, body):
        """Recebe resposta do serviço e envia de volta ao cliente"""
        corr_id = props.correlation_id
        if corr_id is None:
            print("[Coordinator] Resposta sem correlation_id — ignorando")
            return

        client_reply_to = self.pending.pop(corr_id, None)
        if client_reply_to is None:
            print(f"[Coordinator] Nenhum cliente pendente para corr_id={corr_id} — ignorando")
            return

        print(f"[Coordinator] Encaminhando resposta de {corr_id} para {client_reply_to}")

        # publica de volta ao cliente
        self.ch_req.basic_publish(
            exchange='',
            routing_key=client_reply_to,
            properties=pika.BasicProperties(
                correlation_id=corr_id,
                content_type='application/json'
            ),
            body=body
        )

    def start(self):
        # thread para consumir respostas dos serviços
        t_resp = threading.Thread(target=self.ch_resp.start_consuming, daemon=True)
        t_resp.start()

        # consumidor de pedidos do cliente
        self.ch_req.basic_consume(queue=COORDINATOR_QUEUE, on_message_callback=self.on_request, auto_ack=True)
        print("[Coordinator] Aguardando pedidos de clientes na fila 'rpc_coordinator'...")
        try:
            self.ch_req.start_consuming()
        except KeyboardInterrupt:
            print("Coordinator recebeu KeyboardInterrupt. Encerrando...")
            try:
                self.ch_req.stop_consuming()
            except Exception:
                pass
            try:
                self.ch_resp.stop_consuming()
            except Exception:
                pass
            self.conn_req.close()
            self.conn_resp.close()


if __name__ == "__main__":
    coord = Coordinator()
    coord.start()
