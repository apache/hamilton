# hamilton_anthropic.py
import anthropic
import openai

from hamilton.function_modifiers import config


@config.when(provider="openai")
def llm_client__openai() -> openai.OpenAI:
    return openai.OpenAI()


@config.when(provider="anthropic")
def llm_client__anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def joke_prompt(topic: str) -> str:
    return ("Human:\n\nTell me a short joke about {topic}\n\nAssistant:").format(topic=topic)


@config.when(provider="openai")
def joke_response__openai(llm_client: openai.OpenAI, joke_prompt: str) -> str:
    response = llm_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=joke_prompt,
    )
    return response.choices[0].text


@config.when(provider="anthropic")
def joke_response__anthropic(llm_client: anthropic.Anthropic, joke_prompt: str) -> str:
    response = llm_client.completions.create(
        model="claude-2", prompt=joke_prompt, max_tokens_to_sample=256
    )
    return response.completion


if __name__ == "__main__":
    import hamilton_invoke_anthropic
    from hamilton import driver

    dr = (
        driver.Builder()
        .with_modules(hamilton_invoke_anthropic)
        .with_config({"provider": "anthropic"})
        .build()
    )
    dr.display_all_functions("hamilton-anthropic.png")
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))

    dr = (
        driver.Builder()
        .with_modules(hamilton_invoke_anthropic)
        .with_config({"provider": "openai"})
        .build()
    )
    print(dr.execute(["joke_response"], inputs={"topic": "ice cream"}))
