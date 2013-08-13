// ---------------------------------------------------------------------------
// rpc-client
//  This is the client which makes requests to the GPU Processor server. 
// ---------------------------------------------------------------------------
// requries
var amqp = require('amqp');
var amqpUtil = require('./amqp-util');
var uuid = require('uuid');

var connection = amqp.createConnection({ host: 'localhost' });

// generate unique queue name (only do it once)
var queueName = 'rpc-queue' + uuid.v4();

// 1. setup connection
connection.on('ready', function connectionReady(){
    // 2. setup a queue with a unique name
    // Create an exclusive callback queue. This queue is created once per client
    connection.queue(queueName, {exclusive: true}, function setupQueue(queue){
        // keep track of consumer tag to unsubscribe once done
        var consumerTag;

        // 3. subscribe to the created queue
        //  After the server receives, processes, and
        //  publishes a response, this callback will be called
        queue.subscribe(function finishedRPC(msg){
            // 6. Message has been received from the RPC server
            console.log('Message from RPC server: ', msg);
            console.log('To string:', 
                msg.data.toString('utf-8'));

            // unsubscribe from the queue, we're done with it
            queue.unsubscribe(consumerTag);

            // 7. All done
            amqpUtil.safeEndConnection(connection);
        })
        .addCallback(function(ok) { 
            consumerTag = ok.consumerTag; 
        });

        // 4.  After the connection and queue have been set up, we can
        // make RPC requests to the RPC server.
        readyToCall();
    });
});

var readyToCall = function(){
    // Send a message *after* the connection and queue above have been set up
    var message = ((Math.random() * 100000) | 0) + '';
    // get value from command line if passed in
    message = (process.argv[2] || message) + '';

    // 5.  Send request to RPC server
    connection.publish('rpc-queue', message, {
        // use the queue name created above to identify this queue
        replyTo: queueName,
        // generate an ID on each RPC request
        correlationId: uuid.v4(),
        contentType: 'application/json',
        contentEncoding: 'utf-8'
    });
};
