import json
import logging
import os

import requests
from google.cloud import firestore
from google.cloud import pubsub_v1

PROJECT_ID = "sharp-haven-301406"
TOPIC_ID = "tb-tweet-streaming"

logging.basicConfig(level=logging.INFO)


def get_handles():
    """
    Get list of ids of Twitter handles
    Returns:
        List of ids for Twitter handles
    """
    db = firestore.Client()
    h_ref = db.collection(u'tb-handles')
    logging.info("Getting list of handles...")
    docs = h_ref.stream()
    list_of_handles = dict()
    for doc in docs:
        list_of_handles[doc.to_dict()['username']] = doc.to_dict()['id']
    return list_of_handles


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_params():
    """
    Returns:
        List of fields required of tweet objects

    """
    return {"tweet.fields": "id,text,author_id,conversation_id,"
                            "created_at,geo,in_reply_to_user_id,lang,"
                            "public_metrics,source"}


def get_rules(headers):
    """
    Fetching existing rules
    Args:
        headers: Header to pass

    Returns:
        List of existing rules
    """
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
    )
    logging.info("Fetching existing rules...")
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))
    return response.json()


def delete_all_rules(headers, rules):
    """
    Delete existing rules
    Args:
        headers: Header content
        rules: List of rules

    Returns:
        None
    """
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    logging.info("Deleting old rules...")
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    logging.info(json.dumps(response.json()))


def set_rules(headers, handles):
    """
    Set new rules
    Args:
        headers: Header content
        handles: List of handles to filter

    Returns:
        None
    """

    # You can adjust the rules if needed
    rule_str = ''
    for i, h in enumerate(handles):
        if i != len(handles) - 1:
            rule_str = rule_str + '(from:' + h + ') OR '
        else:
            rule_str = rule_str + '(from:' + h + ')'
    sample_rules = [
        # {"value": "from:soumyadip2009 from:twitterdev from:twitterapi from:reuters from: ndtv"},
        # {"value": "(from:reuters) OR (from:soumyadip2009) OR (from:ndtv)"},
        {"value": rule_str}
    ]
    payload = {"add": sample_rules}
    logging.info("Setting new rules...")
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))


def get_stream(headers, rev_handles_dict):
    # Initializing fire store client
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    db = firestore.Client()

    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", headers=headers, stream=True, params=get_params()
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    logging.info("Successfully connected to endpoint.")
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            json_response['data']['username'] = rev_handles_dict[json_response['data']['author_id']]
            # logging.info(json.dumps(json_response, indent=4, sort_keys=True))
            # Data must be a byte string
            response_str = str(json_response["data"]).encode("utf-8")

            # When you publish a message, the client returns a future.
            future = publisher.publish(topic_path, response_str)
            logging.info(future.result())
            logging.info(f"Ingested message to pub sub. Tweet ID: {json_response['data']['id']}")

            doc_ref = db.collection(u'tb-tweets').document(json_response['data']['id'])
            doc_ref.set(json_response['data'])
            logging.info(f"Message written to fire store. Tweet ID: {json_response['data']['id']}")


def main():
    bearer_token = os.environ.get("BEARER_TOKEN")
    headers = create_headers(bearer_token)
    rules = get_rules(headers)
    handles_dict = get_handles()
    rev_handles_dict = {v: k for k, v in handles_dict.items()}
    handles = list(handles_dict.keys())
    delete_all_rules(headers, rules)
    set_rules(headers, handles)
    get_stream(headers, rev_handles_dict)


if __name__ == "__main__":
    main()
