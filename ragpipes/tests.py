from __future__ import annotations

import unittest

from .protocol import TestAction
from .protocol import Workflow

action = TestAction()

workflow1 = Workflow(history=[])

action.run(workflow1, {"w1key": "value"})
action.run(workflow1, {"w1another_key": "another_value"})
action.run(workflow1, {"w1yet_another_key": "yet_another_value"})

workflow1_json = workflow1.model_dump_json()

print(f"WORKFLOW 1 MODEL: {workflow1}")
print(f"WORKFLOW 1 JSON: {workflow1_json}")

workflow2 = Workflow.model_validate_json(workflow1_json)

action.run(workflow2, {"w2key": "value"})
action.run(workflow2, {"w2another_key": "another_value"})
action.run(workflow2, {"w2yet_another_key": "yet_another_value"})

workflow2_json = workflow2.model_dump_json()

print(f"WORKFLOW 2 MODEL: {workflow2}")
print(f"WORKFLOW 2 JSON: {workflow2_json}")


class MainTestCase(unittest.TestCase):

    def test_sum(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
