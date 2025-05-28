from __future__ import annotations

import random
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel

type StageDict = Dict[str, Any]


class Stage(BaseModel):
    name: str
    input: StageDict = dict()
    output: StageDict = dict()
    metadata: StageDict = dict()


class Workflow(BaseModel):
    history: List[Stage]


class Action(BaseModel):
    name: str

    def run(
        self,
        workflow: Workflow,
        input: StageDict,
        metadata: Optional[StageDict] = None,
    ) -> StageDict:
        if metadata is None:
            metadata = {}
        start = time.time()
        output = self._run(workflow, input, metadata)
        time.sleep(random.uniform(0.1, 0.5))  # Simulate some processing time
        time_taken = time.time() - start
        metadata["elapsed"] = time_taken
        stage = Stage(
            name=self.name, input=input, output=output, metadata=metadata
        )
        workflow.history.append(stage)
        return {}


class TestAction(Action):
    name: str = "Test Action"

    def _run(
        self,
        workflow: Workflow,
        input: StageDict,
        metadata: Optional[StageDict] = None,
    ) -> dict:
        if metadata is None:
            metadata = {}
        return {"something": "done", "input": input}


def handler(workflow: Workflow, name: str, input: StageDict) -> Workflow:
    action = TestAction(input=input)
    output = action.run(workflow, input)
    stage = Stage(name=name, input=input, output=output)
    workflow.add_stage(stage)
    return workflow


def do_something(input: StageDict) -> StageDict:
    # Placeholder for actual processing logic
    return {"processed": input}
