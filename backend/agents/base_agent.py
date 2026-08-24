from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Base interface for every ORBIT agent.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, task: str) -> dict:
        """
        Execute the agent's task.

        Every ORBIT agent must implement this method.
        """
        pass
    