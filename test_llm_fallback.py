from types import SimpleNamespace

from llm_fallback import llm_capacity_fallback


class StubClient:
    """Mimics the Anthropic SDK response shape with no network call."""

    def __init__(self, capacity_lbs, input_tokens=50, output_tokens=10):
        self._capacity_lbs = capacity_lbs
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens

    class _Messages:
        def __init__(self, outer):
            self._outer = outer

        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(type="tool_use", input={"capacity_lbs": self._outer._capacity_lbs})],
                usage=SimpleNamespace(
                    input_tokens=self._outer._input_tokens,
                    output_tokens=self._outer._output_tokens,
                ),
            )

    @property
    def messages(self):
        return self._Messages(self)


def demo():
    capacity, cost, latency = llm_capacity_fallback("Rated Load: pounds", client=StubClient(None))
    assert capacity is None
    assert cost == 50 * 1.00 / 1_000_000 + 10 * 5.00 / 1_000_000
    assert latency >= 0

    capacity, cost, latency = llm_capacity_fallback("Rated Load: 3500 pounds", client=StubClient(3500))
    assert capacity == 3500

    print("ok")


if __name__ == "__main__":
    demo()
