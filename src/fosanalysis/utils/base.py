
r"""
Contains abstract base classes.
\author Bertram Richter
\date 2023
"""

from abc import ABC
import warnings

class Base(ABC):
	r"""
	Abstract base class, which deals with superflous constructor arguments. 
	"""
	def __init__(self, *args, **kwargs):
		r"""
		Construct the object and warn about unused/unknown arguments.
		\param *args Additional positional arguments, will be discarded and warned about.
		\param **kwargs Additional keyword arguments, will be discarded and warned about.
		"""
		if len(args) > 0:
			warnings.warn("Unused positional arguments for {c}: {a}".format(c=type(self), a=args))
		if len(kwargs) > 0:
			warnings.warn("Unknown keyword arguments for {c}: {k}".format(c=type(self), k=kwargs))

class Task(Base):
	r"""
	This intermediate class indicates, that a sub-class is implementing a task.
	A task object implements an algorithm to solve specific problem.
	Alternative solution approaches/algorithms, solve the same problem in a different way.
	But task objects for the same problem share the same interface.
	Hence, they are interchangable and enable fine-grained configurability.
	Complex algorithms are composed of several Task objects in Workflow objects.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class Workflow(Base):
	r"""
	This intermediate class indicates, that a sub-class is implementing a workflow.
	Workflow objects implement the order of working steps to solve complex problems.
	The individual working steps are dealt with by Task objects.
	(A Workflow object can serve as a Task object itself in a larger Workflow.)
	
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
