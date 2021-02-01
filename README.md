# tb-tweet-ingestion-streaming

This app connects with Twitter stream API. It fetches real time tweets and process it and push it to PubSub as well as to Firestore.

## How to run:

```shell
export GOOGLE_APPLICATION_CREDENTIALS=/PATH_TO_SERVICE_ACCOUNT_KEY.json

```

*  Now create Kubernetes secrets:
```shell
kubectl create secret generic twitter-battle-key --from-file=key.json=/PATH_TO_SERVICE_ACCOUNT_KEY.json
```

```shell
kubectl create secret generic twitter-battle-twitterdev-key --from-literal=BEARER_TOKEN=TWITTER_DEV_KEY
```

*  Check whether secrets are set properly:
```shell
kubectl get secrets
```
* Deploy containers in K8s cluster:
```shell
kubectl apply -f deployment.yaml
```

*  Check status:
```shell
kubectl get pods
```

*  Delete deployment:
```shell
kubectl delete -f deployment.yaml
```
