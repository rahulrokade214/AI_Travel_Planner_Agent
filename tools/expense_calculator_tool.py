from typing import List
from langchain.tools import tool
from utils.expense_calculator import CalculatorUtils


class CalculatorTool:
    def __init__(self):
        self.calculator = CalculatorUtils()
        self.calculator_tool_list = self._setup_tools()

    def _setup_tools(self):
        """Register all calculator-related tools for the agent."""

        @tool
        def estimate_total_hotel_cost(price_per_night: float, total_days: float) -> float:
            """
            Calculate total hotel cost.
            price_per_night: cost of the hotel per night (numeric)
            total_days: number of nights/days of stay (numeric)
            """
            return self.calculator.estimate_total_hotel_cost(price_per_night, total_days)

        @tool
        def calculate_total_cost(costs: List[float]) -> float:
            """
            Sum up multiple individual cost components (e.g. hotel, food, transport)
            into one total trip cost.
            costs: a list of numeric cost values, e.g. [1200.0, 450.0, 300.0]
            """
            return self.calculator.calculate_total_cost(costs)

        @tool
        def calculate_daily_expense_budget(total_cost: float, days: int) -> float:
            """
            Calculate the average daily budget by dividing total trip cost by
            the number of days.
            total_cost: total estimated cost of the trip (numeric)
            days: number of days of the trip (numeric)
            """
            return self.calculator.calculate_daily_expense_budget(total_cost, days)

        return [estimate_total_hotel_cost, calculate_total_cost, calculate_daily_expense_budget]