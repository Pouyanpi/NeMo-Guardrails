from abc import ABC, abstractmethod
from typing import Dict, Any, List
from . import SPLITTERS

_SPLITTER_MODULE_SUFFIX = "_splitter"
_SPLITTER_REGISTRY = SPLITTERS
_ABSTRACT_SPLITTER_REGISTRY = {}

class RegisteredSplitter(abc.ABC):
  """Subclasses will be registered and given a `name` property."""

  # Name of the splitter, automatically filled if not already set.
  name: ClassVar[str]


  def __init_subclass__(cls, skip_registration=False, **kwargs):  # pylint: disable=redefined-outer-name
    super().__init_subclass__(**kwargs)

    # Set the name if the splitter does not define it.
    # Use __dict__ rather than getattr so subclasses are not affected.
    if not cls.__dict__.get('name'):
      if cls.__name__ == 'Splitter':
        # Config-based splitters should be defined with a class named "Splitter".
        # In such a case, the splitter name is extracted from the module if it
        # follows conventions:
        module_name = cls.__module__.rsplit('.', 1)[-1]
        if module_name.endswith(_SPLITTER_MODULE_SUFFIX):
          cls.name = module_name[: -len(_SPLITTER_MODULE_SUFFIX)]
        elif '.' in cls.__module__:  # Extract splitter name from package name.
          cls.name = cls.__module__.rsplit('.', 2)[-2]
        else:
          raise AssertionError(
              'When using `Splitter` as class name, the document splitter name is '
              'inferred from module name if named "*_splitter" or from '
              f'package name, but there is no package in "{cls.__module__}".'
          )
      else:  
        cls.name = camelcase_to_snakecase(cls.__name__)

    is_abstract = inspect.isabstract(cls)



    # Skip splitter registration within contextmanager, or if skip_registration
    # is passed as meta argument.
    if skip_registration or _skip_registration:
      return

    # Check for name collisions
    if cls.name in _SPLITTER_REGISTRY:
      raise ValueError(f'Splitter with name {cls.name} already registered.')
    elif cls.name in _ABSTRACT_SPLITTER_REGISTRY:
      raise ValueError(
          f'Splitter with name {cls.name} already registered as abstract.'
      )

    # Add the splitter to the registers
    if is_abstract:
      _ABSTRACT_SPLITTER_REGISTRY[cls.name] = cls
    else:
      _SPLITTER_REGISTRY[cls.name] = cls

class SplitterRegistry: 
    def __init__(self) -> None:
        self.splitters = _SPLITTER_REGISTRY
        # self.validate_splitters()

    def __get__(self, class_name: str):
        return self.get(class_name)

    
    def get(self, class_name):
        """
        Get a splitter by name.

        :param class_name: The name of the splitter.
        :raises KeyError: If the splitter name does not exist in the registry.
        """
        if class_name not in self.splitters:
            raise KeyError(f"{class_name} does not exist in the registry")
        return self.splitters.get(class_name)

    def validate_splitters(self) -> None:
        """
        Validate that all splitters have a 'split' method.

        :raises ValueError: If a splitter does not have a 'split' method.
        """
        for splitter_name, splitter in self.splitters.items():
            if not hasattr(splitter, "split_text") or not callable(splitter.split_text):
                raise ValueError(f"{splitter_name} and thus {splitter} does not have a 'split_text' method")
    
    def list(self) -> List[str]:
        """
        List all splitters in the registry.

        :return: A list of splitter names.
        """
        return list(self.splitters.keys())

    def __repr__(self) -> str:
        return f"SplitterRegistry(splitters={self.splitters})"
    
    def __len__(self) -> int:
        return len(self.splitters)
    
    def __iter__(self) -> Iterator[str]:
        return iter(self.splitters)
    
    def __contains__(self, splitter_name: str) -> bool:
        return splitter_name in self.splitters
    
    def __getitem__(self, splitter_name: str) -> Any:
        return self.get(splitter_name)
    






@contextlib.contextmanager
def skip_registration() -> Iterator[None]:
  """Context manager within which dataset builders are not registered."""
  global _skip_registration
  try:
    _skip_registration = True
    yield
  finally:
    _skip_registration = False