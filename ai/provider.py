from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt, user, available_tools):
        """Return a deterministic tool proposal; never execute a tool here."""
