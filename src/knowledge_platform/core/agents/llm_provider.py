"""LLM provider factory supporting OpenAI and compatible APIs."""

from ..config import get_settings


class LLMProvider:
    def __init__(self):
        self._settings = get_settings()
        self._instances: dict = {}

    def get_llm(self, model_tier: str = "mini"):
        cache_key = f"{self._settings.llm_provider}_{model_tier}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        if self._settings.llm_provider == "openai":
            llm = self._create_openai(model_tier)
        elif self._settings.llm_provider == "deepseek":
            llm = self._create_deepseek(model_tier)
        else:
            llm = self._create_openai(model_tier)

        self._instances[cache_key] = llm
        return llm

    def _create_openai(self, model_tier: str):
        from langchain_openai import ChatOpenAI

        model = (
            self._settings.openai_model_gpt4o
            if model_tier == "full"
            else self._settings.openai_model_gpt4o_mini
        )
        kwargs = {
            "model": model,
            "api_key": self._settings.openai_api_key,
            "temperature": 0.7,
        }
        if self._settings.openai_base_url != "https://api.openai.com/v1":
            kwargs["base_url"] = self._settings.openai_base_url
        return ChatOpenAI(**kwargs)

    def _create_deepseek(self, model_tier: str):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self._settings.deepseek_model,
            api_key=self._settings.deepseek_api_key,
            base_url=self._settings.deepseek_base_url,
            temperature=0.7,
        )


provider = LLMProvider()


def get_llm(model_tier: str = "mini"):
    return provider.get_llm(model_tier)
