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
# Setup the OpenCL program and buffers
print 'Setting up CL object and loading data...'
CLProgram = GPU_Processor.CL()
print 'Done!'

# ----------------------------------------------------------------------------
#
# Functionality
#
# ----------------------------------------------------------------------------

# Handle request
# ---------------------------------------
def on_request(ch, method, props, body):
    '''When a request comes in, get the parameters from it and process it on 
    the GPU.  The passed in body is a JSON object with Key / Value pairs of
    Policy Name : Value of Policy
    '''
    income = int(body)
    print "Calling with income: %s"  % (income,)

    # Do the calculations with OpenCL
    result = CLProgram.execute({
        'income': income    
    })

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
