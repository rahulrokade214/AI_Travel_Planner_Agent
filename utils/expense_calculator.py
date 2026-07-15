class CalculatorUtils:
    """
    Core calculation logic for trip expenses.
    All inputs are safely coerced to float/int before arithmetic,
    because LLM tool-calls sometimes pass numbers as strings
    (e.g. "250" instead of 250), which otherwise causes:
        TypeError: can't multiply sequence by non-int of type 'float'
    """

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Expected a numeric value, got: {value!r}")

    def estimate_total_hotel_cost(self, price_per_night, total_days) -> float:
        price = self._to_float(price_per_night)
        days = self._to_float(total_days)
        return price * days

    def calculate_total_cost(self, costs) -> float:
        """costs: a list of numeric cost values to sum."""
        numeric_costs = [self._to_float(c) for c in costs]
        return sum(numeric_costs)

    def calculate_daily_expense_budget(self, total_cost, days) -> float:
        cost = self._to_float(total_cost)
        num_days = self._to_float(days)
        if num_days == 0:
            raise ValueError("Number of days cannot be zero when calculating daily budget.")
        return cost / num_days