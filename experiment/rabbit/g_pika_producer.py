# -*- coding: utf-8 -*-
# This code was copied from the pika documentation
import time
import pika
import json
import logging
import functools
from threading import Thread
from queue import Queue as ThreadQueue
from threading import Event as ThreadEvent

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
    '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class PikaTopicPublisher():
  """
  This is a pika (Python-RabbitMq) message publisher heavily based on the
  asychronous example provided in the pika documentation.  It should handle
  unexpected interactions with RabbitMQ such as channel and connection closures.

  If RabbitMQ closes the connection, an object of this class should reopen it.
  (You should look at the output, as there are limited reasons why the connection
  may be closed, which usually are tied to permission related issues or socket
  timeouts.)

  Example:
    # set a callback mechanism to sample the task's input queue every 1.5 seconds
    # name the exchange in the RabbitMq server at the url to 'g_pika_producer_exchange'
    # name the RabbitMq queue on the server at the url to 'g_queue'
    # set the topic routing key to 'pub_thread.text'
    publisher = \
      PikaTopicPublisher(
        amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
        publish_tempo_sec=1.5,
        exchange_name='g_pika_producer_exchange',
        queue_name='g_queue',
        routing_key='pub_thread.text',
      )

    # to start the thread so pika won't block your code:
    publisher.start_thread()

    # to actually write messages (publish) to the amqp_url:
    publish.post_fifo("Some Message")

    # to stop the thread but keep the connection
    publisher.start_thread()

    # to start the thread again
    publisher.start_thread()

    # to stop the connection and the thread
    publisher.stop()

    # to reconnect and start the thread
    publisher.start_thread()

  Notes:
    It uses delivery confirmations and illustrates one way to keep track of
    messages that have been sent and if they've been confirmed by RabbitMQ.
    This confirmation mechanism will not work if message tempo exceeds the
    publish_tempo (the messages will get through but confirmation mechanism will
    indicate there is a problem when there isn't one.)

    If the input queue has more than one item they will all be sent out to the
    network and the queue sampler callback's frequency will temporarily
    increase to deal with queue bursting.

  """
  EXCHANGE_TYPE             = 'topic'
  PUBLISH_FAST_INTERVAL_SEC = 0.000001  # fast

  def __init__(self,
               amqp_url,
               routing_key,
               publish_tempo_sec,
               exchange_name,
               queue_name):
    """Setup the example publisher object, passing in the URL we will use
    to connect to RabbitMQ.

    :param str amqp_url: The URL for connecting to RabbitMQ

    """
    self._connection = None
    self._channel = None

    self._deliveries = []
    self._acked = 0
    self._nacked = 0
    self._message_number = 0
    self._stopping = False
    self._closing = False

    self._amqp_url = amqp_url
    self._thread_queue = ThreadQueue(maxsize=500)
    self._task_run_event = ThreadEvent()
    self._publish_tempo_sec = publish_tempo_sec

    # will set the exchange, queue and routing_keys names for the RabbitMq
    # server running on amqp_url
    self._rabbit_exchange_name = exchange_name
    self._rabbit_queue_name = queue_name
    self._rabbit_routing_key = routing_key

  def connect(self):
    """This method connects to RabbitMQ, returning the connection handle.
    When the connection is established, the on_connection_open method
    will be invoked by pika. If you want the reconnection to work, make
    sure you set stop_ioloop_on_close to False, which is not the default
    behavior of this adapter.

    :rtype: pika.SelectConnection

    """
    LOGGER.info('Connecting to %s', self._amqp_url)
    return pika.SelectConnection(pika.URLParameters(self._amqp_url),
                   self.on_connection_open,
                   stop_ioloop_on_close=False)

  def on_connection_open(self, unused_connection):
    """This method is called by pika once the connection to RabbitMQ has
    been established. It passes the handle to the connection object in
    case we need it, but in this case, we'll just mark it unused.

    :type unused_connection: pika.SelectConnection

    """
    LOGGER.info('Connection opened')
    self.add_on_connection_close_callback()
    self.open_channel()

  def add_on_connection_close_callback(self):
    """This method adds an on close callback that will be invoked by pika
    when RabbitMQ closes the connection to the publisher unexpectedly.

    """
    LOGGER.info('Adding connection close callback')
    self._connection.add_on_close_callback(self.on_connection_closed)

  def on_connection_closed(self, connection, reply_code, reply_text):
    """This method is invoked by pika when the connection to RabbitMQ is
    closed unexpectedly. Since it is unexpected, we will reconnect to
    RabbitMQ if it disconnects.

    :param pika.connection.Connection connection: The closed connection obj
    :param int reply_code: The server provided reply_code if given
    :param str reply_text: The server provided reply_text if given

    """
    self._channel = None
    if self._closing:
      self._connection.ioloop.stop()
    else:
      LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
               reply_code, reply_text)
      self._connection.add_timeout(5, self.reconnect)

  def reconnect(self):
    """Will be invoked by the IOLoop timer if the connection is
    closed. See the on_connection_closed method.

    """
    self._deliveries = []
    self._acked = 0
    self._nacked = 0
    self._message_number = 0

    # This is the old connection IOLoop instance, stop its ioloop
    self._connection.ioloop.stop()

    # Create a new connection
    self._connection = self.connect()

    # There is now a new connection, needs a new ioloop to run
    self._connection.ioloop.start()

  def open_channel(self):
    """This method will open a new channel with RabbitMQ by issuing the
    Channel.Open RPC command. When RabbitMQ confirms the channel is open
    by sending the Channel.OpenOK RPC reply, the on_channel_open method
    will be invoked.

    """
    LOGGER.info('Creating a new channel')
    self._connection.channel(on_open_callback=self.on_channel_open)

  def on_channel_open(self, channel):
    """This method is invoked by pika when the channel has been opened.
    The channel object is passed in so we can make use of it.

    Since the channel is now open, we'll declare the exchange to use.

    :param pika.channel.Channel channel: The channel object

    """
    LOGGER.info('Channel opened')
    self._channel = channel
    self.add_on_channel_close_callback()
    self.setup_exchange(self._rabbit_exchange_name)

  def add_on_channel_close_callback(self):
    """This method tells pika to call the on_channel_closed method if
    RabbitMQ unexpectedly closes the channel.

    """
    LOGGER.info('Adding channel close callback')
    self._channel.add_on_close_callback(self.on_channel_closed)

  def on_channel_closed(self, channel, reply_code, reply_text):
    """Invoked by pika when RabbitMQ unexpectedly closes the channel.
    Channels are usually closed if you attempt to do something that
    violates the protocol, such as re-declare an exchange or queue with
    different parameters. In this case, we'll close the connection
    to shutdown the object.

    :param pika.channel.Channel: The closed channel
    :param int reply_code: The numeric reason the channel was closed
    :param str reply_text: The text reason the channel was closed

    """
    LOGGER.warning('Channel was closed: (%s) %s', reply_code, reply_text)
    if not self._closing:
      self._connection.close()

  def setup_exchange(self, exchange_name):
    """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
    command. When it is complete, the on_exchange_declareok method will
    be invoked by pika.

    :param str|unicode exchange_name: The name of the exchange to declare

    """
    LOGGER.info('Declaring exchange %s', exchange_name)
    self._channel.exchange_declare(self.on_exchange_declareok,
                     exchange_name,
                     self.EXCHANGE_TYPE)

  def on_exchange_declareok(self, unused_frame):
    """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
    command.

    :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

    """
    LOGGER.info('Exchange declared')
    self.setup_queue(self._rabbit_queue_name)

  def setup_queue(self, queue_name):
    """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
    command. When it is complete, the on_queue_declareok method will
    be invoked by pika.

    :param str|unicode queue_name: The name of the queue to declare.

    """
    LOGGER.info('Declaring queue %s', queue_name)
    self._channel.queue_declare(self.on_queue_declareok, queue_name)

  def on_queue_declareok(self, method_frame):
    """Method invoked by pika when the Queue.Declare RPC call made in
    setup_queue has completed. In this method we will bind the queue
    and exchange together with the routing key by issuing the Queue.Bind
    RPC command. When this command is complete, the on_bindok method will
    be invoked by pika.

    :param pika.frame.Method method_frame: The Queue.DeclareOk frame

    """
    LOGGER.info('Binding %s to %s with %s',
          self._rabbit_exchange_name, self._rabbit_queue_name, self._rabbit_routing_key)
    self._channel.queue_bind(self.on_bindok, self._rabbit_queue_name,
                 self._rabbit_exchange_name, self._rabbit_routing_key)

  def on_bindok(self, unused_frame):
    """This method is invoked by pika when it receives the Queue.BindOk
    response from RabbitMQ. Since we know we're now setup and bound, it's
    time to start publishing."""
    LOGGER.info('Queue bound')
    self.start_publishing()

  def start_publishing(self):
    """This method will enable delivery confirmations and schedule the
    first message to be sent to RabbitMQ

    """
    LOGGER.info('Issuing consumer related RPC commands')
    self.enable_delivery_confirmations()
    self.schedule_next_producer_heart_beat(self._publish_tempo_sec)

  def enable_delivery_confirmations(self):
    """Send the Confirm.Select RPC method to RabbitMQ to enable delivery
    confirmations on the channel. The only way to turn this off is to close
    the channel and create a new one.

    When the message is confirmed from RabbitMQ, the
    on_delivery_confirmation method will be invoked passing in a Basic.Ack
    or Basic.Nack method from RabbitMQ that will indicate which messages it
    is confirming or rejecting.

    """
    LOGGER.info('Issuing Confirm.Select RPC command')
    self._channel.confirm_delivery(self.on_delivery_confirmation)

  def on_delivery_confirmation(self, method_frame):
    """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
    command, passing in either a Basic.Ack or Basic.Nack frame with
    the delivery tag of the message that was published. The delivery tag
    is an integer counter indicating the message number that was sent
    on the channel via Basic.Publish. Here we're just doing house keeping
    to keep track of stats and remove message numbers that we expect
    a delivery confirmation of from the list used to keep track of messages
    that are pending confirmation.

    :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame

    """
    confirmation_type = method_frame.method.NAME.split('.')[1].lower()
    LOGGER.info('Received %s for delivery tag: %i',
          confirmation_type,
          method_frame.method.delivery_tag)
    if confirmation_type == 'ack':
      self._acked += 1
    elif confirmation_type == 'nack':
      self._nacked += 1

    item = method_frame.method.delivery_tag
    # only remove items that exist in our list (if a previous thread was
    # canceled and this one was started we would receive delivery_tags which we
    # didn't send - this could cause the remove method to crash the producer
    if item in self._deliveries:
      self._deliveries.remove(method_frame.method.delivery_tag)
      LOGGER.info('Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked',
            self._message_number, len(self._deliveries),
            self._acked, self._nacked)
    else:
      LOGGER.info('Received delivery tag for something we did not send')

  def schedule_next_producer_heart_beat(self, timeout):
    """If we are not closing our connection to RabbitMQ, schedule another
    message to be delivered in self._publish_tempo_sec seconds.

    """
    if self._stopping:
      return
    # Scheduling next Task queue check
    LOGGER.info('Task queue check in %0.3f seconds', timeout)
    self._connection.add_timeout(timeout, self.producer_heart_beat)

  def publish_message(self, message):
    """If the class is not stopping, publish a message to RabbitMQ,
    appending a list of deliveries with the message number that was sent.
    This list will be used to check for delivery confirmations in the
    on_delivery_confirmations method.

    Once the message has been sent, schedule another message to be sent.
    The main reason I put scheduling in was just so you can get a good idea
    of how the process is flowing by slowing down and speeding up the
    delivery intervals by changing the self._publish_tempo_sec
    constant in the class.

    """
    if self._stopping:
      return

    json_message = {u'json_key': message}
    properties = pika.BasicProperties(app_id='example-publisher',
                      content_type='application/json',
                      headers=json_message)

    self._channel.basic_publish(self._rabbit_exchange_name, self._rabbit_routing_key,
                  json.dumps(message, ensure_ascii=False),
                  properties)
    self._message_number += 1
    self._deliveries.append(self._message_number)
    LOGGER.info('Published message # %i', self._message_number)

  def close_channel(self):
    """Invoke this command to close the channel with RabbitMQ by sending
    the Channel.Close RPC command."""
    LOGGER.info('Closing the channel')
    if self._channel:
      self._channel.close()

  def run(self):
    """Run the example code by connecting and then starting the IOLoop. """
    self._connection = self.connect()
    self._connection.ioloop.start()

  def stop(self):
    """Stop the example by closing the channel and connection and releasing the
    thread. We set a flag here so that we stop scheduling new messages to be
    published. The IOLoop is started because this method is
    invoked by the Try/Catch below when KeyboardInterrupt is caught.
    Starting the IOLoop again will allow the publisher to cleanly
    disconnect from RabbitMQ.
    """
    LOGGER.info('Stopping')
    self._stopping = True
    self.close_channel()
    self.close_connection()
    self._task_run_event.clear()
    self._connection.ioloop.start()
    LOGGER.info('Stopped')

  def close_connection(self):
    """This method closes the connection to RabbitMQ."""
    LOGGER.info('Closing connection')
    self._closing = True
    self._connection.close()

  def producer_heart_beat(self):
    """This is the callback that is called ever publish_tempo_sec to check to
    see if something is in the thread_queue.  If there are items in this queue
    it schedules other callbacks to send out the messages, and temporarily
    increases its frequecy to deal with queue bursting.
    """
    if self._task_run_event.is_set():
      if self._stopping:
        return
      timeout_time = self._publish_tempo_sec
      # messages tend to cluster, they are bursty, so speed up our
      # producer_heart_beat if there were messages in our queue
      queue_length = self._thread_queue.qsize()
      if queue_length != 0:
        timeout_time /= queue_length * 1.0
        # ensure we can output the messages that we are waiting for before we
        # call this producer_heart_beat again (this is just a clamp)
        timeout_time = self.PUBLISH_FAST_INTERVAL_SEC * 2 if timeout_time < self.PUBLISH_FAST_INTERVAL_SEC else timeout_time
      self.schedule_next_producer_heart_beat(timeout_time)

      # send out all messages in the queue
      if queue_length >= 1:
        for i in range(queue_length):
          message = self._thread_queue.get()
          cb = functools.partial(self.publish_message, message=message)
          self._connection.add_timeout(self.PUBLISH_FAST_INTERVAL_SEC, cb)
          LOGGER.info('Scheduling next output message in %0.6f seconds', self.PUBLISH_FAST_INTERVAL_SEC)

  def post_fifo(self, message):
    """use this to post messages to the network"""
    self._thread_queue.put(message)

  def start_thread(self):
    """Add a thread so that the run method doesn't steal our program control."""
    self._task_run_event.set()
    self._stopping = False

    def thread_runner(self):
      # The run method will turn on pika's callback hell.
      # To see how this is turned off look at the producer_heart_beat
      self.run()
      # code here will never run

    thread = Thread(target=thread_runner, args=(self,), daemon=True)
    thread.start()

  def stop_thread(self):
    """stop the thread, but keep the connection open.  To close the connection
    and stop the thread, use the 'stop' api"""
    self._task_run_event.clear()


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
  # send to the raspberry pi
  pub_thread1 = \
    PikaTopicPublisher(
      amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
      routing_key='pub_thread.text',
      publish_tempo_sec=1.5,
      exchange_name='sex_change',
      queue_name='g_queue',
    )
  pub_thread2 = \
    PikaTopicPublisher(
      amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
      routing_key='pub_thread.text',
      publish_tempo_sec=0.5,
      exchange_name='sex_change',
      queue_name='g_queue',
    )
  pub_thread3 = \
    PikaTopicPublisher(
      amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
      routing_key='pub_thread.text',
      publish_tempo_sec=1.1,
      exchange_name='sex_change',
      queue_name='g_queue',
    )
  pub_thread1.start_thread()
  pub_thread2.start_thread()
  pub_thread3.start_thread()

  time.sleep(2)
  for i in range(5):
    pub_thread1.post_fifo("Janice Library {}".format(i))
    pub_thread2.post_fifo("Mervin Burr {}".format(i))
    pub_thread3.post_fifo("Scott {}".format(i))
    time.sleep(0.51)

  pub_thread1.stop_thread()
  pub_thread2.stop_thread()
  pub_thread3.stop()
  time.sleep(3)

  pub_thread1.start_thread()
  pub_thread2.start_thread()
  pub_thread3.start_thread()
  time.sleep(1)

  pub_thread1.post_fifo("Last Message on 1")
  pub_thread2.post_fifo("Last Message on 2")
  print("trying to publish in the new thread runner")
  pub_thread3.post_fifo("Last Message on 3")
  time.sleep(0.5)
  print("hello world")