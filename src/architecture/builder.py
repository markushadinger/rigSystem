from typing import Protocol, runtime_checkable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from src.rig.context import Context
from src.architecture.signal import Signal
from src.lib.naming import Name


@runtime_checkable
class Buildable(Protocol):
    name: Name


class Builder:

    def __init__(self, name):
        self.name = name
        self.modules: list[Buildable] = list()
        self.stages: list[str] = list()
        self.context: Context | None = None
        self.parallel_stages: list[str] = list()

        self.signal_module_started = Signal()
        self.signal_module_ended = Signal()
        self.signal_stage_started = Signal()
        self.signal_stage_ended = Signal()
        self.signal_build_started = Signal()
        self.signal_build_ended = Signal()

    def add_module(self, module: Buildable):
        if module in self.modules:
            return self.modules.index(module)

        self.modules.append(module)
        return module

    def run(self):
        """
        Runs the builder, executing all stages for all modules.
        :return:
        """
        self.populate_context(self.context)

        for stage in self.stages:
            self.run_stage(stage, stage in self.parallel_stages)

        self.signal_build_ended.emit(self.name)

    def run_stage(self, stage: str, parallel: bool = False):
        """
        Runs a specific stage for all modules, sequentially or in parallel.
        :param stage: the name of the stage
        :param parallel: if the stage is parallel
        """
        modules = self.get_modules_with_stage(stage)
        self.signal_stage_started.emit(stage)

        if parallel:
            # Parallel execution with correct signal ordering
            with ThreadPoolExecutor() as executor:
                future_to_module = {}
                for module in modules:
                    self.signal_module_started.emit(stage, str(module.name))
                    future = executor.submit(getattr(module, stage))
                    future_to_module[future] = module

                for future in as_completed(future_to_module):
                    module = future_to_module[future]
                    future.result()  # ensures the stage finished
                    self.signal_module_ended.emit(stage, str(module.name))
        else:
            # Sequential execution
            for module in modules:
                self.signal_module_started.emit(stage, str(module.name))
                getattr(module, stage)()
                self.signal_module_ended.emit(stage, str(module.name))

        self.signal_stage_ended.emit(stage)

    def get_modules_with_stage(self, stage: str) -> list[Buildable]:
        """
        Returns all modules that have a specific stage.
        :param stage: name of the stage
        :return:
        """
        modules = []
        for module in self.modules:
            try:
                getattr(module, stage)
                modules.append(module)
            except AttributeError:
                continue

        return modules

    def __getattr__(self, item):
        return lambda stage=item: self.run_stage(stage)

    def populate_context(self, context: Context):
        for module in self.modules:
            try:
                setattr(module, "context", context)

                if hasattr(module, "populate_context"):
                    getattr(module, "populate_context")(context)
            except RuntimeError:
                continue
