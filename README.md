# OpenCL Processor #
This is an example of how OpenCL could be used as a server to process data based on a static data set and variables sent in by a client.

This example uses PyOpenCL to work with OpenCL.  To communicate between client and server, it uses the RPC paradigm implemented with AMQP. Python, using Pika, acts as the RPC server, and we have a NodeJS client which sends requests (the client could be any implementation of AMQP). This example uses RabbitMQ.

Specifically, there are three files:
1. `GPU_Processor.py`: This file using PyOpenCL to run calculations. It exposes a CL class, which is used by the RPC server
2. `GPU_RPC_Server.py`: Uses Pika to create a RPC server. When the server starts up, it creates a new CL object, which loads data. Then, whenever a RPC request is received, it calls execute() which handles recreating the OpenCL program string based on the passed in parameters and executing the code.
3 `rpc-client.js`: An AMQP rpc client written in Node.  Sends a message to the server with a parameter, waits on a response, then returns it. Will pass in a random value, or you can call `node rpc-client.js 1234` where `1234` is the value you want to send to the rpc server

## Use Case ##
The problem this example attempts to solve is running a series of (fairly simple) calculations on a non trivially large (target size is 100million records) data set (that can fit into memory) as quickly as possible (ideally, in realtime).  The base data is static (in my case, a dump of data from a database), but calculations need to be run based on input parameters.  

Specifically, this examples enables a server to be running that can respond to requests from a client (e.g., a user on a website) and return the result. We use the Remote Procedure Call (RPC) paradigm to achieve this. Using queues, we can be sure that multiple clients can make a request at the same time and (eventually) get back a response.


### Potential Problems ###
If your data is too big to fit into memory or speed is not a requirement, the map reduce paradigm may be better suited.  If your data set is a bit smaller (e.g., hundreds of thousands) records, a simplier solution using NodeJS or Python (PyPy / NumPy) / etc. may be a better solution. 
