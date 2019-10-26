# Serverless framework

## インストール

```
$ node -v
v8.16.0

$ npm --version
6.4.1

$ npm install -g serverless

$ sls -v
1.42.1
```

## プラグイン インストール

```
$ npm install --save serverless-python-requirements
$ sls plugin install -n serverless-pseudo-parameters
```

## Python モジュールインストール

```
$ sudo pip install requests
$ sudo pip install boto3
```

## ローカル実行

```
$ sls invoke local -f index --path event/event.json
```

## デプロイ

```
$ sls deploy -v --stage dev
$ sls deploy -v --stage prd
```

## リソースの削除

```
$ sls remove -v
```

## Systems Manager パラメータストアの登録

dev.GOOGLE_APIKEY、prd.GOOGLE_APIKEY をパラメータストアに登録する。

# StepFunctions

## 動作確認
入力オプションに下記を入力する

```
{
  "location": "35.030595080487956,135.71524145459694"
}
```

# API Gateway

## 動作確認 AWS コンソール画面でのテスト

### exec

```
{
  "input": "{\"location\": \"35.030595080487956,135.71524145459694\"}",
  "name": "test-201905021800",
  "stateMachineArn": "arn:aws:states:ap-northeast-1:<AWSアカウントID>:stateMachine:FindCatsInStreetView-dev-state"
}
{
  "input": "{\"location\": \"35.03062404438918,135.71523072576088\"}",
  "name": "test-201905031420",
  "stateMachineArn": "arn:aws:states:ap-northeast-1:<AWSアカウントID>:stateMachine:FindCatsInStreetView-dev-state"
}
```

### status

```
{
  "executionArn": "arn:aws:states:ap-northeast-1:<AWSアカウントID>:execution:FindCatsInStreetView-dev-state:test-201905021810"
}
```

