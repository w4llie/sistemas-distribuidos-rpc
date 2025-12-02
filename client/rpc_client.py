import uuid
import json
import threading
from common.rpc_utils import get_connection
import pika

class RpcClient:
    def __init__(self):
        self.connection = get_connection()
        self.channel = self.connection.channel()

        self.coordinator_queue = 'rpc_coordinator'

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.response = None
        self.corr_id = None

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.consume_thread = threading.Thread(target=self._start_consuming, daemon=True)
        self.consume_thread.start()

    def _start_consuming(self):
        try:
            self.channel.start_consuming()
        except Exception:
            pass

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, service_name: str, payload: dict, timeout: float = 10.0):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        message = {
            "service": service_name,
            "payload": payload
        }

        self.channel.basic_publish(
            exchange='',
            routing_key=self.coordinator_queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                content_type='application/json',
            ),
            body=json.dumps(message)
        )

        import time
        waited = 0.0
        interval = 0.05
        while self.response is None and waited < timeout:
            time.sleep(interval)
            waited += interval

        if self.response is None:
            raise TimeoutError("Timeout waiting for RPC response")

        return json.loads(self.response)

if __name__ == "__main__":
    import sys

    cli = RpcClient()

    print("Escolha o serviço: soma, media, busca")
    service = input("Serviço: ").strip()

    if service == "soma":
        a = float(input("a: "))
        b = float(input("b: "))
        payload = {"a": a, "b": b}
    elif service == "media":
        nums = input("Números separados por espaço: ")
        payload = {"numbers": [float(x) for x in nums.split()]}
    elif service == "busca":
        key = input("Termo de busca (string): ")
        payload = {"term": key}
    else:
        print("Serviço desconhecido")
        sys.exit(1)

    print(f"Chamando serviço '{service}' com payload: {payload}")
    resp = cli.call(service, payload)
    print("Resposta:", resp)