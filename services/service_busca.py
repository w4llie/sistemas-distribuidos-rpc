# services/service_busca.py
import pika
import json
import time
from common.rpc_utils import get_connection

QUEUE = 'service_busca'

FAKE_DB = {
    "python": ["Tutorial Python", "PEP8 guide"],
    "rabbitmq": ["Tutorial RabbitMQ", "Exemplo RPC"],
    "ia": ["Introdução à IA"]
}

def process(payload):
    term = payload.get("term","").lower()
    time.sleep(1)
    return {"matches": FAKE_DB.get(term, [])}

def main():
    conn = get_connection()
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE)

    def on_request(ch, method, props, body):
        try:
            msg = json.loads(body)
            payload = msg.get("payload", {})
            client_corr_id = msg.get("client_corr_id") or props.correlation_id
        except Exception as e:
            print("Formato inválido:", e)
            return

        print(f"[service_busca] Recebido corr_id={client_corr_id} payload={payload}")
        result = process(payload)
        response_body = json.dumps(result)

        reply_to = props.reply_to
        ch.basic_publish(
            exchange='',
            routing_key=reply_to,
            properties=pika.BasicProperties(
                correlation_id=client_corr_id,
                content_type='application/json'
            ),
            body=response_body
        )
        print(f"[service_busca] Respondido corr_id={client_corr_id}")

    ch.basic_consume(queue=QUEUE, on_message_callback=on_request, auto_ack=True)
    print("[service_busca] Aguardando mensagens na fila 'service_busca'...")
    ch.start_consuming()

if __name__ == "__main__":
    main()
