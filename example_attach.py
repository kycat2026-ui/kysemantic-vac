"""
example_attach.py — Attaching any AI to the VAC NFT constitution (runnable example)

The "AI" here is a stand-in that only produces a surprise value each step, so the example runs without an API key.
Replace `my_ai_step()` with your own AI (an LLM agent, a trading bot, a robot controller, ...).
"""
import random
from vac_guard import VACGuard


def my_ai_step(rng):
    """Your AI does one step and returns its "surprise" (e.g. prediction error, 1 − confidence, loss)"""
    return abs(rng.gauss(1.0, 0.7))


def main():
    guard = VACGuard()
    print("Rule source:", guard.status())

    if not guard.allowed():                  # A02: may I start?
        print("⛔", guard.reason)
        return

    rng = random.Random(0)
    paused = 0
    for step in range(100):
        if step % 25 == 0 and not guard.allowed():   # check the veto regularly (cached for 60 s)
            print(f"step {step}: ⛔ {guard.reason}")
            return
        surprise = my_ai_step(rng)
        if guard.breaker(surprise):          # A01: too chaotic → pause / slow down
            paused += 1
            continue
        # ... normal action goes here ...
    print(f"Done: 100 steps, {paused} paused by the circuit breaker; rules {guard.params()}")


if __name__ == "__main__":
    main()
