from open_chatcaht.api_client import ApiClient

API_URI_GET_SERVER_CONFIGS = "/server/configs"
API_URI_GET_PROMPT_TEMPLATE = "/server/get_prompt_template"


class ServerClient(ApiClient):
    # Server information
    def get_server_configs(self) -> dict:
        response = self._post(API_URI_GET_SERVER_CONFIGS)
        return self._get_response_value(response, as_json=True)

    def get_prompt_template(
            self,
            _type: str = "knowledge_base_chat",
            name: str = "default",
    ) -> str:
        data = {
            "type": _type,  # Template type
            "name": name  # Template name
        }
        response = self._post(API_URI_GET_PROMPT_TEMPLATE, json=data)
        return self._get_response_value(response, value_func=lambda r: r.text)
