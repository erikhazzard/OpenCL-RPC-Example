''' =======================================================================
    GPU Processor
        Exposes functionality which the GPU-rpc-server will use.
        Using pyOpenCL to handle processing
    ======================================================================= '''
import random
import sys
import os
from util import timing

import pyopencl as cl
import numpy

''' =======================================================================

    Functionality

    ======================================================================= '''
# ----------------------------------------------------------------------------
#
# Data loader
#
# ----------------------------------------------------------------------------
num_items = 20000
def load_data():
    '''Loads tax data and creates NumPy arrays for it
    '''
    data_dict = {
        'income': numpy.array(xrange(num_items), dtype=numpy.float32),
        'cap': numpy.array(xrange(num_items), dtype=numpy.float32),
    }

    return data_dict

class CL:
    def __init__(self):
        self.data = load_data()

        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)

        self.setup_buffers()

    def setup_buffers(self):
        '''Sets up the data arrays and buffers. This needs to happen 
        only once, as the data itself does not change
        '''

        #initialize client side (CPU) arrays
        timing.timings.start('buffer')
        print 'Setting up data arrays'

        self.data1 = self.data['income']
        self.data2 = self.data['cap']
        timing.timings.stop('buffer')
        print 'Done setting up two numpy arrays in %s ms | (%s seconds)' % (
            timing.timings.timings['buffer']['timings'][-1],
            timing.timings.timings['buffer']['timings'][-1] / 1000
        )

        #create OpenCL buffers
        timing.timings.start('buffer')

        mf = cl.mem_flags
        self.data1_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.data1)
        self.data2_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=self.data2)
        self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, self.data2.nbytes)
        timing.timings.stop('buffer')

        print 'Done setting up buffers in %s ms' % (
            timing.timings.timings['buffer']['timings'][-1]
        )

    def load_program(self, params):
        ''' Create the .cl program to use. This needs to get regenerated at each
        request, as the values used change based on the request
        '''

        #Generate a .cl program
        program = """__kernel void worker(__global float* data1, __global float* data2, __global float* result)
        {
            unsigned int i = get_global_id(0);
            float d1 = data1[i];
            float d2 = data2[i];
        """

        # Define calculations
        program += """result[i] = d1 * d2 * {income};
        """.format(
                income=params['income']
            )

        program += "}" 

        #create the program
        self.program = cl.Program(self.ctx, program).build()


    def execute(self, params):
        ''' This handles the actual execution for the processing, which would
        get executed on each request - this is where we care about the
        performance
        '''
        timing.timings.start('execute')

        self.load_program(params)

        # Start the program
        self.program.worker(self.queue, 
            self.data1.shape, 
            None, 
            self.data1_buf, 
            self.data2_buf, 
            self.dest_buf,
        )

        # Get an empty numpy array in the shape of the original data
        result = numpy.empty_like(self.data1)

        #Wait for result
        cl.enqueue_read_buffer(self.queue, self.dest_buf, result).wait()

        #show timing info
        timing.timings.stop('execute')
        finish = timing.timings.timings['execute']['timings'][-1]
        print '<<< DONE in %s' % (finish)
        return result

# Execute it
# ---------------------------------------
if __name__ == "__main__":
    # Test that execute works when calling this directly passing in a param
    example = CL()

    example.execute({ 'income': 42 })

    timer = timing.timings.timings['execute']
    avg = (timer['total'] ) / timer['count']

    print 'Average time for execute: %s milliseconds | (%s seconds)' % (avg, avg / 1000)
