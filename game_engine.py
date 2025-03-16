from typing import Dict, List, Optional
# import json
from tokenize_and_parse import tokenize, parse
from evaluate import evaluate
from all_namespace import namespace


class HackingScenario:
    def __init__(self, name: str, description: str, goal: str, initial_code: str,
                 success_condition: Dict, available_commands: List[str]):
        self.name = name
        self.description = description
        self.goal = goal
        self.initial_code = initial_code
        self.success_condition = success_condition
        self.available_commands = available_commands
        self.completed = False


class GameEngine:
    def __init__(self):
        self.scenarios = self.load_scenarios()
        self.current_scenario: Optional[HackingScenario] = None
        self.names = namespace()

    def load_scenarios(self) -> List[HackingScenario]:
        return [
            HackingScenario(
                "Security Override",
                "Вам преграждает запертая бронированная дверь. Напишите сценарий, чтобы обойти ее.",
                "Создайте функцию, которая генерирует правильную последовательность переопределения.",
                "(определить последовательность переопределения (lambda (x) (* x 1337)))",
                {"target_value": 1337},
                ["override", "scan", "bypass"]
            ),
            HackingScenario(
                "Camera Hack",
                "Отключите систему видеонаблюдения, воспользовавшись ее интерфейсом управления.",
                "Напишите сценарий, который последовательно отключает все камеры.",
                "(определение режима отключения камеры (lambda (id) (+ id 42)))",
                {"required_output": 42},
                ["disable", "loop", "execute"]
            )
        ]

    def evaluate_code(self, code: str) -> str:
        try:
            tokens = tokenize(code)
            parsed = parse(tokens)
            result = evaluate(parsed, self.names)

            if self.current_scenario:
                if self.check_success_condition(result):
                    self.current_scenario.completed = True
                    return f"SUCCESS! {self.current_scenario.name} completed!"

            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def check_success_condition(self, result) -> bool:
        if not self.current_scenario:
            return False

        condition = self.current_scenario.success_condition
        if "target_value" in condition:
            return result == condition["target_value"]
        elif "required_output" in condition:
            return result == condition["required_output"]
        return False

    def start_scenario(self, index: int) -> str:
        if 0 <= index < len(self.scenarios):
            self.current_scenario = self.scenarios[index]
            return f"""
Mission: {self.current_scenario.name}
{self.current_scenario.description}

Goal: {self.current_scenario.goal}

Available commands: {', '.join(self.current_scenario.available_commands)}

Initial code:
{self.current_scenario.initial_code}
"""
        return "Invalid scenario index"
