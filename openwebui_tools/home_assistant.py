import requests
from pydantic import Field


class Tools:
    def __init__(self):
        pass

    def home_assistant_query(
        self,
        message: str = Field(
            ...,
            description="Ask anything about Home Assistant sensors in natural language",
        ),
    ) -> str:
        """
        Query Home Assistant via FastAPI bridge and return sensor values.
        """

        # Your FastAPI bridge URL
        url = "http://192.168.1.107:8000/chat"

        try:
            # Send POST request to your bridge
            response = requests.post(url, json={"message": message}, timeout=10)

            # If request failed
            if response.status_code != 200:
                return f"Error from bridge API: {response.text}"

            data = response.json()

            # Return only the response text
            return data.get("response", "No response returned from Home Assistant.")

        except Exception as e:
            return f"Request failed: {str(e)}"
