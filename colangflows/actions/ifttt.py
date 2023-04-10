from langchain.tools.ifttt import IFTTTWebhook


class IFTTT(IFTTTWebhook):
    tool_input: str

    def run(self):
        """Route query to _run() of langchain tool."""

        return self._run(self.tool_input)
