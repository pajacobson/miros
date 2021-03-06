import re
import time
import logging
from functools import wraps
from functools import partial
from collections import deque
from collections import namedtuple

from miros import Event
from miros import spy_on
from miros import signals
from miros import Factory
from miros import return_status
from miros import HsmWithQueues

def instrumented(fn):
  '''wrapper for the parallel regions states

    **Note**:
       It hide any hidden state from appearing in the instrumentation

    **Args**:
       | ``fn`` (function): the state function


    **Returns**:
       (function): wrapped function

    **Example(s)**:
      
    .. code-block:: python
       
       @instrumented
       def example(p, e):
        status = return_status.UNHANDLED
        return status
  '''
  @wraps(fn)
  def _pspy_on(chart, *args):
    if chart.instrumented:
      status = spy_on(fn)(chart, *args)
      for line in list(chart.rtc.spy):
        m = re.search(r'hidden_region', str(line))
        if not m:
          chart.outer.live_spy_callback(
            "{}::{}".format(chart.name, line))
      chart.rtc.spy.clear()
    else:
      e = args[0] if len(args) == 1 else args[-1]
      status = fn(chart, e)
    return status
  return _pspy_on

@instrumented
def s1_hidden_region(r, e):
  '''A hidden state which permits the exit feature of the
     s1_region to work.

    **Note**:
       This will not appear in the spy instrumentation

    **Args**:
       | ``p`` (HsmWithQueues): Hsm with queues with no thread
       | ``e`` (Event): event


    **Returns**:
       (type): return_status
  '''
  status = return_status.UNHANDLED
  if(e.signal == signals.to_p):
    status = r.trans(s1_region)
  else:
    r.temp.fun = r.top
    status = return_status.SUPER
  return status

@instrumented
def s1_region(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.INIT_SIGNAL):
    status = r.trans(s11)
  elif(e.signal == signals.region_exit):
    status = r.trans(s1_hidden_region)
  else:
    r.temp.fun = s1_hidden_region
    status = return_status.SUPER
  return status

@instrumented
def s11(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.e4):
    status = r.trans(s12)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  else:
    r.temp.fun = s1_region
    status = return_status.SUPER
  return status

@instrumented
def s12(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.INIT_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.e1):
    status = r.trans(s1_region_final)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  else:
    r.temp.fun = s1_region
    status = return_status.SUPER
  return status

@instrumented
def s1_region_final(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    r.final = True
    r.post_p_final_to_outer_if_ready()
  elif(e.signal == signals.ENTRY_SIGNAL):
    r.final = False
  else:
    r.temp.fun = s1_region
    status = return_status.SUPER
  return status

@instrumented
def s2_hidden_region(r, e):
  '''A hidden state which permits the exit feature of the
     s2_region to work.

    **Note**:
       This will not appear in the spy instrumentation

    **Args**:
       | ``p`` (HsmWithQueues): Hsm with queues with no thread
       | ``e`` (Event): event


    **Returns**:
       (type): return_status
  '''
  status = return_status.UNHANDLED
  if(e.signal == signals.to_p):
    status = r.trans(s2_region)
  else:
    r.temp.fun = r.top
    status = return_status.SUPER
  return status

@instrumented
def s2_region(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.INIT_SIGNAL):
    status = r.trans(s21)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.region_exit):
    status = r.trans(s2_hidden_region)
  else:
    r.temp.fun = s2_hidden_region
    status = return_status.SUPER
  return status

@instrumented
def s21(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.e1):
    status = r.trans(s22)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  else:
    r.temp.fun = s2_region
    status = return_status.SUPER
  return status

@instrumented
def s22(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    status = return_status.HANDLED
  elif(e.signal == signals.e2):
    status = r.trans(s2_region_final)
  elif(e.signal == signals.EXIT_SIGNAL):
    status = return_status.HANDLED
  else:
    r.temp.fun = s2_region
    status = return_status.SUPER
  return status

@instrumented
def s2_region_final(r, e):
  status = return_status.UNHANDLED
  if(e.signal == signals.ENTRY_SIGNAL):
    r.final = True
    r.post_p_final_to_outer_if_ready()
  elif(e.signal == signals.ENTRY_SIGNAL):
    r.final = False
  else:
    r.temp.fun = s2_region
    status = return_status.SUPER
  return status

class Region(HsmWithQueues):

  def __init__(self, name, starting_state, outer, final_event, instrumented=True):
    '''Region management for othogonal regions

    **Args**:
       | ``name`` (str): name of the region
       | ``starting_state`` (str): name of the starting
       |   state of the region
       | ``outer`` (Factory): The statechart which will be
       |   using this region.
       | ``final_event`` (Event): The event used to finalize 
       |   the region.
       | ``instrumented=True`` (bool): Need if you want to
       |   view the spy instrumention

    **Returns**:
       (Region): a region in the statechart

    **Example(s)**:
      
    .. code-block:: python
       
      self.s1_region = Region(
        's1_r',
        outer=self,
        final_event=Event(signal=signals.p_final),
      )
      self.p_regions.append(self.s1_region)

    '''
    super().__init__()
    self.name = name
    self.starting_state = starting_state
    self.outer = outer
    self.final_event = final_event
    self.instrumented = instrumented

    self.final = False
    self.regions = []

  def post_p_final_to_outer_if_ready(self):
    ready = False if self.regions is None and len(self.regions) < 1 else True
    for region in self.regions:
      ready &= True if region.final else False
    if ready:
      self.outer.post_fifo(self.final_event)

class InstrumentedFactory(Factory):
  def __init__(self, name, *, log_file=None, live_trace=None, live_spy=None):
    super().__init__(name)
    self.live_trace = False if live_trace == None else live_trace
    self.live_spy = False if live_spy == None else live_spy
    self.log_file = 'xml_chart.log' if log_file == None else log_file

    self.clear_log()

    logging.basicConfig(
      format='%(asctime)s %(levelname)s:%(message)s',
      filename=self.log_file,
      level=logging.DEBUG)

    self.register_live_spy_callback(partial(self.spy_callback))
    self.register_live_trace_callback(partial(self.trace_callback))

  def trace_callback(self, trace):
    '''trace without datetimestamp'''
    trace_without_datetime = re.search(r'(\[.+\]) (\[.+\].+)', trace).group(2)
    logging.debug("T: " + trace_without_datetime)

  def spy_callback(self, spy):
    '''spy with machine name pre-pending'''
    self.print(spy)
    logging.debug("S: [{}] {}".format(self.name, spy))

  def clear_log(self):
    with open(self.log_file, "w") as fp:
      fp.write("")

class XmlChart(InstrumentedFactory):
  def __init__(self, name, live_trace=None, live_spy=None):
    '''Example of othogonal regions described in the CSXML
       standard

    **Args**:
       | ``name`` (type1): 
       | ``live_trace=None``: enable live_trace feature?
       | ``live_spy=None``: enable live_spy feature?

    **Returns**:
       (type): 

    **Example(s)**:
      
    .. code-block:: python
       
        example = XmlChart(
          'parallel', live_spy=True, live_trace=True
        ).start()

    '''
    super().__init__(name, live_trace=live_trace, live_spy=live_spy)

    self.p_regions = []
    self.p_regions.append(
      Region(
        name='s1_r',
        starting_state=s1_hidden_region,
        outer=self,
        final_event=Event(signal=signals.p_final),
      )
    )
    self.p_regions.append(
      Region(
        name='s2_r',
        starting_state=s2_hidden_region,
        outer=self,
        final_event=Event(signal=signals.p_final),
      )
    )
    for region in self.p_regions:
      for _region in self.p_regions:
        region.regions.append(_region)

    self.outer_state = self.create(state="outer_state"). \
      catch(signal=signals.ENTRY_SIGNAL,
        handler=self.outer_state_entry_signal). \
      catch(signal=signals.to_p,
        handler=self.outer_state_to_p). \
      to_method()

    self.p = self.create(state="p"). \
      catch(signal=signals.ENTRY_SIGNAL,
        handler=self.p_entry_signal). \
      catch(signal=signals.e1,
        handler=self.p_dispatcher). \
      catch(signal=signals.e2,
        handler=self.p_dispatcher). \
      catch(signal=signals.e4,
        handler=self.p_dispatcher). \
      catch(signal=signals.p_final,
        handler=self.p_p_final). \
      catch(signal=signals.EXIT_SIGNAL,
        handler=self.p_exit_signal). \
      catch(signal=signals.to_outer,
        handler=self.p_to_outer). \
      to_method()

    self.some_other_state = self.create(state="some_other_state"). \
      catch(signal=signals.ENTRY_SIGNAL,
        handler=self.some_other_state_entry_signal). \
      to_method()

    self.nest(self.outer_state, parent=None). \
      nest(self.p, parent=self.outer_state). \
      nest(self.some_other_state, parent=self.outer_state)

  def start(self):
    for region in self.p_regions:
      region.start_at(region.starting_state)
    super().start_at(self.outer_state)
    return self

  def outer_state_entry_signal(self, e):
    status = return_status.HANDLED
    return status

  def outer_state_to_p(self, e):
    self.live_spy_callback("to_p:outer_state")
    status = self.trans(self.p)
    return status

  def p_entry_signal(self, e):
    status = return_status.HANDLED
    self.p_dispatcher(Event(signal=signals.to_p))
    return status

  def p_dispatcher(self, e):
    status = return_status.HANDLED
    self.live_spy_callback("{}:p".format(e.signal_name))
    [region.post_fifo(e) for region in self.p_regions]
    [region.complete_circuit() for region in self.p_regions]
    return status

  def p_p_final(self, e):
    status = self.trans(self.some_other_state)
    return status

  def p_exit_signal(self, e):
    status = return_status.HANDLED
    self.p_dispatcher(Event(signal=signals.region_exit))
    return status

  def p_to_outer(self, e):
    self.live_spy_callback("to_outer:p")
    status = self.trans(self.outer_state)
    return status

  def some_other_state_entry_signal(self, e):
    import pdb; pdb.set_trace()
    status = return_status.HANDLED
    return status

if __name__ == '__main__':

  example = XmlChart(
    'parallel', 
    live_spy=True
  ).start()

  example.post_fifo(Event(signal=signals.to_p))
  example.post_fifo(Event(signal=signals.e4))
  example.post_fifo(Event(signal=signals.e1))
  example.post_fifo(Event(signal=signals.to_outer))
  example.post_fifo(Event(signal=signals.to_p))
  example.post_fifo(Event(signal=signals.e4))
  example.post_fifo(Event(signal=signals.e1))
  example.post_fifo(Event(signal=signals.e2))
  time.sleep(100.10)

