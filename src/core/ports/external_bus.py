import abc
import json
from typing import Dict
from boto3 import client

from apolo import config


class AbstractExternalBus(abc.ABC):
    @abc.abstractmethod
    def publish(self, context: str, message_type: str, message: Dict):
        raise NotImplementedError


class SQSExternalBus(AbstractExternalBus):
    def __init__(self):
        self.client = client("sqs")

    def publish(self, context: str, message_type: str, message: Dict):
        body = dict(
            context=context, message_type=message_type, message=message
        )
        self.client.send_message(
            QueueUrl=config.get_envar("SQS_URL"), MessageBody=json.dumps(body)
        )
