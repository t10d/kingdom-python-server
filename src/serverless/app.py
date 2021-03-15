import asyncio
import json
from logging import getLogger
from typing import Dict, Any, Callable

from apolo import config
from craftship.federation import federation


ELB_RESOLVER = {
    ("mov-pub-listener", "POST"): {"context": "management", "type": "mov-pub"}
}


ELB_RESPONSE = {
    "statusCode": 200,
    "statusDescription": "200 OK",
    "isBase64Encoded": False,
    "headers": {"Content-Type": "application/json"},
    "body": None,
}


def init_apolo():
    params: Dict[str, Dict] = {
        "local": dict(start_orm=False),
        "sandbox": dict(start_orm=True),
        "staging": dict(start_orm=True),
        "prod": dict(start_orm=True),
    }
    env = config.current_environment()
    logger = getLogger(__name__)
    logger.info(f"Apolo Serverless @ {env}")
    return federation(**params[env])


class Handler:
    context_resolver = None

    def __init__(self, init_function=init_apolo):
        # lambda holds recent global variables in /tmp so we only need to
        # federate if there is no hanging around resources
        if not Handler.context_resolver:
            _, Handler.context_resolver = init_function()

    def __call__(self, aws_event, lambda_context, source=None):
        """
        >>> body = {
        >>>     "context": "search",
        >>>     "type": "fetch-search",
        >>>     "payload": {
        >>>         "data_sources": ["neoway", "bigdata"],
        >>>         "documents": ["12345678910", "12345678911"]
        >>>     }
        >>> }
        >>> event = {
        >>>     "Records": [
        >>>         {
        >>>             "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
        >>>             "receiptHandle": "MessageReceiptHandle",
        >>>             "body": f"{json.dumps(body)}",
        >>>             "attributes": {
        >>>                 "ApproximateReceiveCount": "1",
        >>>                 "SentTimestamp": "1523232000000",
        >>>                 "SenderId": "123456789012",
        >>>                 "ApproximateFirstReceiveTimestamp": "1523232000001"
        >>>             },
        >>>             "messageAttributes": {},
        >>>             "md5OfBody": "{{{md5_of_body}}}",
        >>>             "eventSource": "aws:sqs",
        >>>             "eventSourceARN": "arn:aws:123456789012:MyQueue",
        >>>             "awsRegion": "us-east-2"
        >>>         }
        >>>     ]
        >>> }
        >>> handler(event, {})
        """
        if source == "ELB":
            try:
                env, path, *_ = filter(
                    lambda p: bool(p), aws_event["path"].split("/")
                )
            except ValueError:
                return ELB_RESPONSE
            method = aws_event["httpMethod"]
            event_info = ELB_RESOLVER.get((path, method), None)
            if not event_info:
                return ELB_RESPONSE

            context, _type = event_info["context"], event_info["type"]
            event_resolver = Handler.context_resolver[context][_type]
            event_parameters = {
                "query": aws_event["queryStringParameters"],
                "body": aws_event["body"],
            }
            loop = asyncio.get_event_loop()
            loop.run_until_complete(event_resolver(**event_parameters))
            return ELB_RESPONSE


handler = Handler()
handler_elb: Callable[[Dict, Any], Dict] = lambda evt, ct: handler(
    evt, ct, "ELB"
)
