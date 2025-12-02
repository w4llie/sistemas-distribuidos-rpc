# services/service_soma.py
import json
import time
import pika
from common.rpc_utils import get_connection

QUEUE = 'service_soma'


def process(payload):
    a = payload.get("a", 0)
    b = payload.get("b", 0)
    # simula trabalho
    time.sleep(1)
    return {"result": a + b}


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

        print(f"[service_soma] Recebido corr_id={client_corr_id} payload={payload}")
        result = process(payload)
        response_body = json.dumps(result)

        # responder para o reply_to (coordinator_responses)
        reply_to = props.reply_to
        if reply_to is None:
            print(f"[service_soma] Nenhum reply_to fornecido, não posso responder corr_id={client_corr_id}")
            return

        ch.basic_publish(
            exchange='',
            routing_key=reply_to,
            properties=pika.BasicProperties(
                correlation_id=client_corr_id,
                content_type='application/json'
            ),
            body=response_body
        )
        print(f"[service_soma] Respondido corr_id={client_corr_id}")

    ch.basic_consume(queue=QUEUE, on_message_callback=on_request, auto_ack=True)
    print(f"[service_soma] Aguardando mensagens na fila '{QUEUE}'...")
    ch.start_consuming()


if __name__ == "__main__":
    main()
