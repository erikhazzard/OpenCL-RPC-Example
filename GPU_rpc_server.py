#-----------------------------------------------------------------------------
# GPU-rpc-server
#   Handles communication between the GPU processing script and communication
#   back to the original caller using AMQP and the RPC pattern
#-----------------------------------------------------------------------------
import pika
import GPU_Processor
import time

# Config 
# ---------------------------------------
QUEUE_NAME = 'rpc-queue'

# Setup connection and queue 
# ---------------------------------------
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost')
)
channel = connection.channel()
channel.queue_declare(queue='%s' % (QUEUE_NAME))

# Load data
# ---------------------------------------
print 'Loading data...'
data = GPU_Processor.load_data()
print 'Data loaded!', data

# Setup the OpenCL program and buffers
CLProgram = GPU_Processor.CL()
CLProgram.load_program()
CLProgram.setup_buffers()

# ----------------------------------------------------------------------------
#
# Functionality
#
# ----------------------------------------------------------------------------

# Handle request
# ---------------------------------------
def on_request(ch, method, props, body):
    n = int(body)
    print " [.] fib(%s)"  % (n,)
    response = n

    # Do the calculations with OpenCL
    result = CLProgram.execute()

    # Publish a message using the passed in routing key and correlation ID 
    ch.basic_publish(exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=str(result),
    )
    # acknowledge delivery
    ch.basic_ack(delivery_tag = method.delivery_tag)

# Start it up
# ---------------------------------------
channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc-queue')

print 'Starting RPC Server ...'
channel.start_consuming()
