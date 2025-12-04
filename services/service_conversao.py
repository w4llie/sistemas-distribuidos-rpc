import json
import time
import pika
from common.rpc_utils import get_connection

QUEUE = 'service_conversao'

def process(payload):
    celsius = payload.get("celsius", 0.0)
    fahrenheit = celsius * 1.8 + 32
    time.sleep(0.1)
    return {"resultado em fahrenheit": fahrenheit}

def main():
    conn = get_connection()
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE)

    def on_request(ch, method, props, body):
        try:
            payload = json.loads(body)
            client_corr_id = props.correlation_id
        except Exception as e:
            print("Formato inválido:", e)
            return

        print(f"[{QUEUE}] Recebido corr_id={client_corr_id} payload={payload}")
        result = process(payload)
        response_body = json.dumps(result)

        reply_to = props.reply_to
        if reply_to is None:
            print(f"[{QUEUE}] Nenhum reply_to fornecido, não posso responder corr_id={client_corr_id}")
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
        print(f"[{QUEUE}] Respondido corr_id={client_corr_id}")

    ch.basic_consume(queue=QUEUE, on_message_callback=on_request, auto_ack=True)
    print(f"[{QUEUE}] Aguardando mensagens na fila '{QUEUE}'...")
    ch.start_consuming()

if __name__ == "__main__":
    main()
