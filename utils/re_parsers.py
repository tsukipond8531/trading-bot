import json

from flask import request


def validate_response(response):
    if isinstance(response, dict):
        return response
    else:
        raise ValueError(f"response is not DICT! {response}")


class ResponseParser:

    def __init__(self, response: dict):
        self.response = validate_response(response)
        self.simple_response = self.simple_response()

    def simple_response(self):
        return {
            "status": self.response.get('status', None),
            "symbol": self.response.get('symbol', None),
            "amount": self.response.get('amount', None),
            "average": self.response.get('average', None),
            "cost": self.response.get('cost', None),
            "price": self.response.get('price', None),
            "side": self.response.get('side', None),
            "reduce_only": self.response.get('reduceOnly', None),
            "type": self.response.get('type', None),
            "fees": self.response.get('fees', None),
            "fee": self.response.get('fee', None)
        }

    def respond(self):
        return {
            'status': self.simple_response['status'],
            'side': self.simple_response['status']
        }


class RequestParser:

    def __init__(self):
        self.request = self.get_content()

    @staticmethod
    def get_content():
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            return request.json
        else:
            return json.loads(request.data)

    @property
    def exchange(self):
        return str.lower(self.request['exchange'])

    @property
    def market(self):
        return str.upper(self.request['market'])

    @property
    def action(self):
        return str.lower(self.request['action'])

    @property
    def let_me_in(self):
        return str(self.request['pass'])
