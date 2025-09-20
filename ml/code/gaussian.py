import tensorflow as tf
"""
Apply gaussian filter to a symbolic tensor.

src: https://stackoverflow.com/a/65219530
"""

def get_gaussian_kernel(shape=(3,3), sigma=0.5):
    # Calculate center coordinates
    m,n = [(ss-1.)/2. for ss in shape]
    # Create coordinate grids
    x = tf.expand_dims(tf.range(-n,n+1,dtype=tf.float32),1)
    y = tf.expand_dims(tf.range(-m,m+1,dtype=tf.float32),0)
    # Apply gaussian formula
    h = tf.exp(tf.math.divide_no_nan(-((x*x) + (y*y)), 2*sigma*sigma))
    # Normalize kernel
    h = tf.math.divide_no_nan(h,tf.reduce_sum(h))
    return h

def gaussian_blur(inp, shape=(3,3), sigma=0.5):
    # Get number of input channels
    in_channel = tf.shape(inp)[-1]
    # Generate gaussian kernel
    k = get_gaussian_kernel(shape,sigma)
    # Expand kernel for all channels
    k = tf.expand_dims(k,axis=-1)
    k = tf.repeat(k,in_channel,axis=-1)
    k = tf.reshape(k, (*shape, in_channel, 1))
    # Apply convolution
    conv = tf.nn.depthwise_conv2d(inp, k, strides=[1,1,1,1],padding="SAME")
    return conv