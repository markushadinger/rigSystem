import time

from src.architecture.builder import Builder

import logging


class Monitor:
    def __init__(self, builder: Builder):
        self.builder = builder
        self.builder.signal_module_started.connect(self.on_module_started)
        self.builder.signal_module_ended.connect(self.on_module_ended)
        self.builder.signal_stage_started.connect(self.on_stage_started)
        self.builder.signal_stage_ended.connect(self.on_stage_ended)
        self.builder.signal_build_started.connect(self.on_build_started)
        self.builder.signal_build_ended.connect(self.on_build_ended)

        self.module_time_stamps = {}
        self.stage_time_stamps = {}

        self.logger = logging.getLogger(self.builder.name)


    def on_module_started(self, stage: str, module_name: str):
        self.logger.info(f"{stage}: {module_name}")
        timestamp = time.time()
        self.module_time_stamps.setdefault(stage, {})[module_name] = timestamp

    def on_module_ended(self, stage: str, module_name: str):
        timestamp = time.time()
        self.module_time_stamps[stage][module_name] = timestamp - self.module_time_stamps[stage][module_name]

    def on_stage_started(self, stage: str):
        self.logger.info(f"Started stage {stage}")
        timestamp = time.time()
        self.stage_time_stamps[stage] = timestamp

    def on_stage_ended(self, stage: str):
        timestamp = time.time()
        self.stage_time_stamps[stage] = timestamp - self.stage_time_stamps[stage]

    def on_build_started(self, builder_name: str):
        self.logger.info(f"---------------- BUILD STARTED {builder_name} ----------------")

    def on_build_ended(self, builder_name: str):
        self.logger.info(f"---------------- BUILD COMPLETE {builder_name} ----------------")
        self.print_time_stamps()

    def get_stage_time(self, stage: str) -> float:
        return sum(self.module_time_stamps[stage].values())

    def print_time_stamps(self):
        # determine longest labels for alignment
        stage_width = max(len(stage) for stage in self.module_time_stamps)
        module_width = max(len(module) for modules in self.module_time_stamps.values() for module in modules)

        for stage, modules in self.module_time_stamps.items():
            stage_time = self.stage_time_stamps[stage]
            print(f"{stage:<{stage_width}}{stage_time:>8.3f}s")

            for module, time_taken in modules.items():
                print(f"  - {module:<{module_width}}{time_taken:>8.3f}s")

        end = "total:"
        time_taken = sum(self.stage_time_stamps.values())
        print(f"{end:<{module_width}}{time_taken:>8.3f}s")
