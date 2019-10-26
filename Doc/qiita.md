# Google ストリートビューで猫を探すシステムを作ってみた
#AWS #python #GoogleAPI  #個人開発

Google ストリートビューに写り込んだ猫を探せたら、めっちゃカワイイ猫がざくざく見つかるんじゃないかと思って、そんなことが出来るシステムを作ってみた。

結果から言うと、画像を解析するのに時間がかかって地図上の狭い範囲しか解析できないし、AWS Rekognition の料金がかさんで、
一般に公開してガンガン検索されるとクラウド破産する、ということがわかった。
とりあえず API Gateway の使用量プランでリクエスト回数を制限して公開してみる。
また、ストリートビューで猫はなかなか見つからないということがわかった。
他にもわかったこととか、使った技術をまとめておく。

## 使い方

[FindCatsInStreetView](https://find-cats.kaotil.com/index.html) にアクセスして、検索した場所をクリックして、Find Cats ボタンを押す。
処理中はくるくる表示が出ます。30秒ほどお待ちください。
処理が終わるとと Google Map 上に検索した経路が赤線で表示されます。
猫とか動物が見つかった地点にはマークが付いて、マークをクリックすると画像を見ることが出来ます。

初期表示される地図は福岡県の相島です。ここではちょこちょこ猫が見つかりました。
恵比寿神社をクリックすると確実に猫が見つかります。
猫島で有名な宮城県の田代島では、あんまり猫が見つけられませんでした。

<img width="1505" alt="find_cats_02.png" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/128902/7a8d9225-850e-7574-2e95-f6fef2c0ba30.png">

注意1) 料金の関係で週100回程度しか実行できないよう API Gateway の使用量プランで制限しています。制限を超えている場合は403エラーとなります。

## システムの構成

CloudFront 経由で S3 にある静的サイトを表示する。
JavaScript で API Gateway を呼び出して、Step Function 経由で Lambda を実行する。
Lambda から Google Street View の API で画像を取得し、Rekognition で画像解析する。
API Gateway は29秒でタイムアウトしてしまうので、API Gateway と Lambda の間に Step Functions を間に入れました。
Step Function を間に入れると、タスクのステータスと Lambda の実行結果を取得できます。
こちらを参考にしました。
[【API Gatewayタイムアウト対策】Step Functionsを組み合わせて非同期処理にしてみる](https://dev.classmethod.jp/cloud/aws/apigateway-stepfunctions-asynchronous/)

![インフラ構成図.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/128902/4dc859b0-823a-5262-5ca9-50f54c331b8a.png)

1つ失敗したと思ったのは、
Step Functions を実行する際に実行名というユニークな値を指定するんですが、それを `p-緯度-経度` にしたこと。
そうすると、同じ緯度経度で2回目の検索はすでに Lambda を実行して結果を持っているので速攻で結果を返せるんですが、
1回目でエラーになると、2回目以降もエラーしか返せなくなってしまいました。
年月日時分秒+ランダムな文字列 とかにした方がよかったです。

### アクセス制限とセキュリティ的な対応

- CloudFront から S3 はオリジンアクセスアイデンティティで CloudFront からのアクセスのみ許可
- API Gateway は API キーを使用
- JavaScript を難読化する
  - API キーを簡単には見えないようにしておく
- Google API キーで制限
  - Lambda 用 API キー
      - 呼び出せる API を制限
          - Roads API
          - Street View Static API
  - 画面用の API キー
      - リファラを指定
      - 呼び出せる API を制限
          - Maps JavaScript API
- 外部に知られたくない情報は Systems Manager パラメータストアに登録する
  - Lambda で使用する Google API KEY や、WAF で許可する IP アドレスなど
- 開発環境は WAF で IP 制限する

## Lambda ファンクション

指定された緯度経度の近辺のストリートビュー画像を取得して、画像に猫が写っていたら S3 にアップロードして検索結果を返す。
cat だけだとなかなか見つからないので、dog, animal, pet なども検索対象とする。
Serverless Framework を使って AWS ほとんどのリソースを作成しています。

[FindCatsInStreetview Serverless](https://github.com/kaotil/FindCatsInStreetview/tree/master/Serverless)

#### 処理概要

1. 指定の緯度経度を 0.0002(約20m) づつ座標を足した座標を計算する
1. 計算した緯度経度が道路でない場合もあるので Google Maps Roads API で位置情報を道路上の位置に補正する
1. 各地点でストリートビューの東西南北の画像を取得する
1. 取得した画像を AWS Rekognition で画像解析する
1. 解析結果に Cat とか Pet とか Animal とか Dog が含まれているかチェックする
1. 含まれていたら S3 に画像をアップロードする
1. 検索結果を返す

## AWS の料金

#### Rekognition

[Amazon Rekognition の料金](https://aws.amazon.com/jp/rekognition/pricing/)

- 無料枠
  - 最初の12か月間は、1か月あたり 5,000枚の画像分析と、毎月最大 1,000個の顔メタデータの保存
- 有料枠
  - 月100万枚までの料金 1,000枚あたり $1.3

1回のリクエストで約64枚の画像を解析するので、
無料枠では、だいたい月に 78回(5000 / 64 = 78.125)くらいの検索しかできない。

週に100回実行を許可する場合、$33ほどかかってしまうけどとりあえずこんくらいを許容する。

64枚 * 400回 = 25600枚
25600 - 5000 = 20600 / 1000 = 20.6
21 * $1.3 = $27.3

#### API Gateway

[Amazon API Gateway の料金](https://aws.amazon.com/jp/api-gateway/pricing/)

- 無料枠
  - API コール受信数 100 万件、メッセージ数 100 万件、接続時間 750,000 分/月
- 有料枠
  - 100万リクエストあたり$4.25

Rekognition で料金がかさむので使用量プランを使って呼び出される回数を制限する。

- API Gateway 使用量プラン
  - 310リクエスト/週に設定

1回の検索で、Lambda 実行のリクエスト1回と1秒おきのステータスチェックが30回くらい呼び出されるのので、約31回の呼び出し。
週に100回の検索を許容するとして、週に100回の検索で310回、月に1240回の呼び出しとなる。
1240回なら余裕で無料枠。

API Gateway のキャッシュを有効にすると料金がまぁまぁかかるので注意。

#### Step Functions

[AWS Step Functions の料金](https://aws.amazon.com/jp/step-functions/pricing/)

- 無料枠
  - 4,000回の状態遷移
- 有料枠
  - $0.025/1,000回

1回の実行で3回状態遷移する。
月400回だと1200回の状態遷移なので無料枠内でおさまる。

#### Lambda

[AWS Lambda 料金](https://aws.amazon.com/jp/lambda/pricing/)

- 無料枠
  - 1,000,000件のリクエスト
  - コンピューティング時間 400,000 GB/秒 (メモリが1GBの場合400,000秒が無料)

Lambda ファンクションのメモリは 1024MBにしているので400,000秒(111.111111時間)が無料。
余裕で無料枠におさまる。

#### Data Transfer

[Amazon EC2 料金表](https://aws.amazon.com/jp/ec2/pricing/on-demand/)

Lambda で猫画像が見つかった場合 S3 にインターネット経由で画像をアップロードする際のデータ転送に料金がかかる。
また CloudFront のエッジノードからインターネットと CloudFront からオリジンへのデータ転送にも料金がかかる。
料金は、EC2 データ転送料金になる。

- 無料枠
  - 1GB
- 有料枠
  - 9.999TB/月まで、$0.114/GB

請求書を見ると、無料枠の1GBはリージョンごとに1GB無料っぽい。
1画像が50KB程度で、1回の検索で多めに5枚の猫画像が見つかったとして、月に400回の検索で2000画像、97.66MBで$11になる。
実際にはそんなに猫見つからないので無料枠でおさまると思う。

50KB * 2000画像 = 100000KB = 97.66MB
97.66MB * $0.114 = $11.13324

#### CloudFront

[Amazon CloudFront の料金](https://aws.amazon.com/jp/cloudfront/pricing/)

エッジロケーションごとにこまかく料金が違うが、概算がわかればよいので日本だけで見る。

- インターネットへのリージョンデータ転送アウト (GB 単位)
  - 10TB まで $0.114
- オリジンへのリージョン内データ転送アウト (GB 単位)
  - すべてのデータ転送 $0.060
- HTTP メソッドのリクエスト料金 (1 万件あたり)
  - HTTP リクエスト、$0.0090
  - HTTPS リクエスト、$0.0120

1画像が50KB程度で、1回の検索で多めに5枚の猫画像が見つかったとして、月に400回の検索で2000画像、97.66MBとなる。
10TB $0.114なので微々たるもんになりそう。
50KB * 2000画像 = 100000KB = 97.66MB

HTTP メソッドのリクエストは、100万リクエスト来ても$1とかなんで、こちらも微々たるもんになりそう。

#### WAF & Shield

[AWS WAF の料金](https://aws.amazon.com/jp/waf/pricing/)

- ウェブ ACL
    - $5/月
- ルール
    - $1/月

開発環境の IP 制限で、1 ウェブACLと1ルールを使用しているので、$6/月。

#### 請求アラーム

$50 を超えたらメールが来るよう設定しておく。

## Google Maps Platform の料金
#### Google Maps API

[マップ、ルート、プレイスの料金設定](https://cloud.google.com/maps-platform/pricing/sheet/?hl=ja)

1か月$200分の無料クレジット

- Street View Static API
    - 最大 28,000 パノラマが無料、以降 0～100,000 は $7.00/1000回
- Roads API
    - 最大 20,000 呼び出しが無料、以降 0～100,000 は $10.00/1000回
- Maps JavaScript API
    - 最大 100,000 読み込みが無料、以降 0～100,000 は $2.00/1000回

#### API の呼び出し回数の制限

無料枠を超えないようにざっくり設定しておく。

- Street View Static API
  - 5,000/日
- Roads API
  - 1,000/日
- Maps JavaScript API
  - 5,000/日

#### 予算アラート

1ヶ月の予算を設定して、予算の50%、90%、100%を超えたらメールが来るよう設定しておく。