import json
import time
from common.rpc_utils import get_connection
import pika

QUEUE = 'service_media'

def process(payload):
    nums = payload.get("numbers", [])
    if not nums:
        return {"error": "no numbers provided"}
    time.sleep(2)
    avg = sum(nums) / len(nums)
    return {"result": avg, "count": len(nums)}

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

        print(f"[service_media] Recebido corr_id={client_corr_id} payload={payload}")
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
        print(f"[service_media] Respondido corr_id={client_corr_id}")

    ch.basic_consume(queue=QUEUE, on_message_callback=on_request, auto_ack=True)
    print("[service_media] Aguardando mensagens na fila 'service_media'...")
    ch.start_consuming()

if __name__ == "__main__":
    main()